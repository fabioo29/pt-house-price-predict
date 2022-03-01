import os
import requests

HEADERS = requests.get('https://httpbin.org/anything').json()['headers']

MAX_POOLSIZE = 1

DISTRICTS = ['aveiro', 'beja', 'braga', 'braganca', 'castelo-branco', 'coimbra', 'evora', 'faro', 'guarda',
             'leiria', 'lisboa', 'portalegre', 'porto', 'santarem', 'setubal', 'viana-do-castelo', 'vila-real', 'viseu']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = 'https://www.idealista.pt/'
DISTRICT_URL = 'https://www.idealista.pt/en/comprar-casas/{}-distrito/pagina-{}?ordem=atualizado-desc'

VALUES = {
    'type': 'detached house, semi-detached house, terraced house, andar de moradia, floor, estate, apartment',
    'condition': 'second hand/needs renovating, second hand/good condition, new housing development',
    'features': 'fitted wardrobes, air conditioning, terrace, balcony, storeroom, parking space included in the price, with lift, swimming pool, garden, garage, construction year, reduced mobility',
    'heating_type': 'individual heating, central heating: gas, no heating'
}
