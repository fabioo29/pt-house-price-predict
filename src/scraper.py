import os
import re
import time
import httpx
import pyproj
import asyncio
import requests
import datetime
import shapefile
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from argparse import ArgumentParser
from shapely.geometry import Point, Polygon
from webdriver_manager.utils import ChromeType
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from utils import HEADERS, DISTRICTS, MAX_POOLSIZE, BASE_URL, DISTRICT_URL, VALUES, BASE_DIR

aux_vars = [time.time(), 0, False]

def coords_helper():
    """Get data to help on the convertion from coordinates to location info"""

    rg_names = ['continente', 'acores_central',
                'acores_ocidental', 'acores_oriental', 'madeira']

    coords_parser_dir = os.path.join(BASE_DIR, 'data', 'coords_parser')
    zip_files = os.listdir(coords_parser_dir)

    # unzip zip_files
    for zip_file in zip_files:
        os.system(
            f'unzip -qq {os.path.join(coords_parser_dir, zip_file)} -d {coords_parser_dir}')

    rg_data = []
    for rg_name in rg_names:
        rg_data.append([
            open(os.path.join(coords_parser_dir, rg_name + '.prj'), "r").read(),
            shapefile.Reader(os.path.join(coords_parser_dir, rg_name + '.shp'))
        ])

    for file in os.listdir(coords_parser_dir):
        if file not in zip_files:
            os.remove(os.path.join(coords_parser_dir, file))

    return rg_data


async def get_session(is_user):
    """get session cookie from the driver"""

    chrome_options = Options()
    if not is_user:
        chrome_options.add_argument("--headless")

    driver_path = ChromeDriverManager(
        chrome_type=ChromeType.CHROMIUM).install()
    driver = webdriver.Chrome(
        driver_path, service_log_path=os.devnull, options=chrome_options)

    driver.get(BASE_URL)
    print('\n')

    while 'A network change was detected' in driver.page_source or \
        (
            "ct.captcha-delivery.com" not in driver.page_source or \
            "class='id-logo'" not in driver.page_source
        ):
        driver.get(BASE_URL)

    if "ct.captcha-delivery.com" in driver.page_source:
        if not is_user:
            driver.quit()
            raise Exception(
                f"DEBUG: Captcha detected. Please run the script with --user flag. {' '*30}")
        print(
            f"DEBUG: Captcha detected, waiting for user interaction... {' '*30}", end="\r")
        time.sleep(1)
    else:
        driver.find_element_by_class_name("id-logo").click()
    time.sleep(1)

    session = httpx.AsyncClient(headers=HEADERS, timeout=None)
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    driver.quit()
    return session


async def get_listings(client, district):
    """get all available house listings urls in Portugal"""

    houses_urls = set()
    url = DISTRICT_URL.format(district, 1)
    while True:
        while True:
            r = await client.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            if soup.select('.selected'):
                break

        # get all the houses hrefs from the current page
        curr_houses = set([el['href'] for el in soup.select('.item-link')])
        houses_urls = houses_urls.union(curr_houses)
        aux_vars[1] += len(curr_houses)

        elapsed = str(datetime.timedelta(
            seconds=int(time.time() - aux_vars[0])))
        print(
            f"DEBUG: {aux_vars[1]} houses found in {elapsed}... {' '*30}", end='\r')

        # get next page url if it exists
        try:
            url = BASE_URL + soup.select('.next > a')[0]['href']
        except IndexError:
            return houses_urls


async def scrape_house_data(client, link, old_houses, regions):
    """scrape house data from the given page link"""

    r = await client.get(link)
    soup = BeautifulSoup(r.content, 'html.parser')

    try:
        soup.select('.date-update-text')[0].text.split('updated')[-1].strip()
    except IndexError:
        return

    coords = re.findall(r"itude\W+(-?\d+\.\d+)", str(r.content))
    try:
        for region in regions:
            TransformationPoint = pyproj.transform(pyproj.CRS(
                "EPSG:4326"), region[0], float(coords[0]), float(coords[1]))
            TransformationPoint = Point(TransformationPoint)

            location = []
            for shapeRec in region[1].shapeRecords():
                poly = Polygon(shapeRec.shape.points)
                if poly.contains(TransformationPoint):
                    location = shapeRec.record
                    break

            if location:
                break
    except IndexError:
        return

    try:
        curr_house = {
            'district': location[3],
            'county': location[2],
            'parish': location[1],
        }
    except IndexError:
        curr_house = {
            'district': 'NONE',
            'county': 'NONE',
            'parish': 'NONE',
        }

    features = soup.select('.details-property_features > ul > li')
    features = [el.text.lower().strip() for el in features]

    curr_house.update({
        'url': link,
        'rooms': re.search(r'T(\d)', soup.text).groups()[0],
        'fitted_wardrobes': 'fitted wardrobes' in features,
        'air_conditioning': 'air conditioning' in features,
        'terrace': 'terrace' in features,
        'balcony': 'balcony' in features,
        'storeroom': 'storeroom' in features,
        'with_lift': 'with lift' in features,
        'swimming_pool': 'swimming pool' in features,
        'garden': 'garden' in features,
        'garage': 'garage' in features,
        'green_area': 'green areas' in features,
        'reduced_mobility': None,
        'price': re.search(r'((\d+(,)?)*\d+) €', soup.text).groups()[0]
    })

    try:
        curr_house['condition'] = list(
            filter(lambda x: x.lower() in VALUES['condition'], features))[0].strip()
    except IndexError:
        curr_house['condition'] = 'land'

    try:
        curr_house['bathrooms'] = re.search(
            r'(\d) bathroom', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['bathrooms'] = None

    try:
        curr_house['type'] = list(
            filter(lambda x: x.lower() in VALUES['type'], features)
        )[0].strip()
    except IndexError:
        curr_house['type'] = 'Apartment'

    try:
        curr_house['built_area'] = re.search(
            r'(\d+) m² built', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['built_area'] = None

    try:
        curr_house['usable_area'] = re.search(
            r'(\d+) m² floor', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['usable_area'] = None

    try:
        curr_house['plot_area'] = re.search(
            r'Land plot of (\d+) m²', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['plot_area'] = None

    try:
        curr_house['floors'] = re.search(
            r'(\d+)\w+ floor', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['floors'] = None

    try:
        curr_house['energy_efficiency'] = soup.select(
            'span[class^="icon-energy"]'
        )[0]['title']
    except IndexError:
        curr_house['energy_efficiency'] = None

    try:
        curr_house['heating_type'] = list(
            filter(lambda x: 'heating' in x.lower(), features)
        )[0].strip()
    except IndexError:
        curr_house['heating_type'] = None

    try:
        curr_house['construction_year'] = re.search(
            r'Built in (\d+)', soup.text
        ).groups()[0]
    except AttributeError:
        curr_house['construction_year'] = None

    return curr_house


async def main(loop, is_user: bool = False, regions: list = None):
    """async main function"""

    # get session cookie from get_session() in async
    client = await get_session(is_user)
    print(f"DEBUG: Session cookies saved... {' '*30}")

    houses_urls = set()
    if DISTRICTS:
        tasks = {
            loop.create_task(
                get_listings(client, DISTRICTS.pop())
            )
        }
        while tasks:
            done,  tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            while True:
                if not DISTRICTS or len(tasks) >= MAX_POOLSIZE:
                    break
                tasks.add(
                    loop.create_task(
                        get_listings(client, DISTRICTS.pop())
                    )
                )
            for task in done:
                houses_urls = houses_urls.union(task.result())
            elapsed = str(datetime.timedelta(
                seconds=int(time.time() - aux_vars[0])))
            print(
                f"DEBUG: {len(houses_urls)} houses found in {elapsed}... {' '*30}", end='\r')

    old_houses = pd.DataFrame()
    data_dir = os.path.join(os.path.join(BASE_DIR, 'data', 'houses.csv'))
    if os.path.exists(data_dir):
        old_houses = pd.read_csv(data_dir)

    houses = pd.DataFrame(
        columns=[
            'url', 'district', 'county', 'parish', 'type',
            'condition', 'built_area', 'usable_area', 'plot_area',
            'rooms', 'bathrooms', 'energy_efficiency', 'floors',
            'fitted_wardrobes', 'air_conditioning', 'terrace', 'balcony',
            'storeroom', 'with_lift', 'swimming_pool', 'garden', 'garage',
            'construction_year', 'heating_type', 'reduced_mobility', 'price'
        ]
    )

    print(f"DEBUG: {aux_vars[1]} houses found in {elapsed}.{' '*30}")

    aux_vars[0] = time.time()
    total_houses = len(houses_urls)
    if houses_urls:
        tasks = {
            loop.create_task(
                scrape_house_data(
                    client, BASE_URL + houses_urls.pop(), old_houses, regions
                )
            )
        }
        while tasks:
            done,  tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            while True:
                if not houses_urls or len(tasks) >= MAX_POOLSIZE:
                    break
                tasks.add(
                    loop.create_task(
                        scrape_house_data(
                            client, BASE_URL + houses_urls.pop(), old_houses, regions
                        )
                    )
                )
            for task in done:
                houses = houses.append(task.result(), ignore_index=True)

            elapsed = str(datetime.timedelta(
                seconds=int(time.time() - aux_vars[0])))
            print(
                f"DEBUG: {total_houses-len(houses_urls)}/{total_houses} houses scraped in {elapsed}... {' '*30}", end='\r')
    print(
        f"DEBUG: {total_houses-len(houses_urls)}/{total_houses} houses scraped in {elapsed}... {' '*30}")

    houses = pd.concat([old_houses, houses]).drop_duplicates(
        subset=['url'], keep='last')
    houses.to_csv(os.path.join(BASE_DIR, 'data', 'houses.csv'), index=False)
    await client.aclose()

def runner():
    parser = ArgumentParser()
    parser.add_argument('-u', '--user', action='store_true', dest='user')
    args = parser.parse_args()

    regions = coords_helper()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, args.user, regions))

if __name__ == '__main__':
    runner()
