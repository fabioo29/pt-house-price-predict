import requests
import tempfile
import base64
import time
import pandas as pd

from subprocess import Popen, PIPE
from scraper import runner as Scraper

aux_vars = [time.time(), 0, False]

try:
    vpn_data = requests.get("http://www.vpngate.net/api/iphone/").text.replace("\r", "")
    servers = [line.split(",") for line in vpn_data.split("\n")]
    labels = servers[1]
    labels[0] = labels[0][1:]
    servers = [s for s in servers[2:] if len(s) > 1]
    df = pd.DataFrame(servers, columns=labels)
except BaseException:
    print("Cannot get VPN servers data")
    exit(1)

# must be possible to connect via OpenVPN
df = df[df['OpenVPN_ConfigData_Base64'].notnull()]

# fix typos score
df['Score'] = df['Score'].str.replace(',', '.').astype(float)

while True:
    """test each VPN connection on the scrapper"""
    try:
        winner = df.sort_values(by='Uptime', ascending=True).iloc[0]
        df = df[df.index != winner.name]

        _, path = tempfile.mkstemp()

        f = open(path, "w")
        f.write(base64.b64decode(winner[-1]).decode())
        f.write(
            "\nscript-security 2\nup /etc/openvpn/update-resolv-conf\ndown /etc/openvpn/update-resolv-conf"
        )
        f.close()

        process = Popen(["sudo", "openvpn", "--config", path], stdout=PIPE)

        while True:
            output = process.stdout.readline()
            
            if output == '' and process.poll() is not None:
                break

            if output:
                curr_txt = output.strip()

                # print(str(curr_txt))
                # if VPN is successfully connected, initialize scrapper
                if 'Initialization Sequence Completed' in str(curr_txt):
                    print(f"VPN: {winner['IP']} from {winner['CountryLong']} working. {len(df)} left{' '*30}")
                    Scraper()
                    process.kill() # kill process

                    while process.poll() != 0:
                        time.sleep(1)
                        break

                elif "process" in str(curr_txt):
                    raise Exception(
                f"VPN: {winner['IP']} from {winner['CountryLong']} not working. {len(df)} left{' '*30}")

        rc = process.poll()

    except Exception as e:
        if 'Captcha detected' in str(e) or 'VPN:' in str(e):
            print(str(e) + '\n')
            pass
        else:
            raise(e)