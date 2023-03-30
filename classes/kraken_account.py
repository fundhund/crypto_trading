import time
import requests
import urllib.parse
import hashlib
import hmac
import base64

with open("keys/kraken.txt", "r") as f:
    lines = f.read().splitlines()
    api_key = lines[0]
    api_sec = lines[1]

base_url = "https://api.kraken.com"

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def kraken_request(url_path, data, api_key, api_sec):
    headers = {"API-Key": api_key, "API-Sign": get_kraken_signature(url_path, data, api_sec)}
    response = requests.post((base_url + url_path), headers=headers, data=data)
    return response

to_kraken_symbols = {
    "btc": "xbt",
}

from_kraken_symbols = {v: k for k, v in to_kraken_symbols.items()}

def to_kraken_symbol(symbol):
    return to_kraken_symbols.get(symbol, symbol).upper()

def from_kraken_symbol(symbol):
    return from_kraken_symbols.get(symbol.lower(), symbol)

class KrakenAccount:
    def __init__(self):
        pass

    def get_eur_balance(self):
        try:
            url_path = "/0/private/Balance"
            data = {"nonce": str(int(1000 * time.time()))}
            response = kraken_request(url_path, data, api_key, api_sec)
            response_json = response.json()
            if not response.ok or response_json["error"]:
                return None
            else:
                eur_balance = response_json["result"]["ZEUR"]
                return float(eur_balance)
        except:
            return None

    # todo
    def buy(self, currency_symbol, amount_in_eur):
        pass

    # todo
    def sell_all(self, currency_symbol):
        pass
