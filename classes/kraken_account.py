import time
import requests
import urllib.parse
import hashlib
import hmac
import base64
from classes.log_helper import log

with open("keys/kraken.txt", "r") as f:
    lines = f.read().splitlines()
    api_key = lines[0]
    api_sec = lines[1]

base_url = "https://api.kraken.com"

def get_kraken_signature(urlpath, data):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(api_sec), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def kraken_request(url_path, data):
    headers = {"API-Key": api_key, "API-Sign": get_kraken_signature(url_path, data)}
    response = requests.post((base_url + url_path), headers=headers, data=data)
    return response


def handle_request(url_path, data):
    response = kraken_request(url_path, data)
    
    if not response.ok:
        log(f"ERROR: Request failed with status code {response.status_code}")
        return None
    
    response_json = response.json()
    
    if response_json["error"]:
        log(f"ERROR: {response_json['error']}")
        return None

    result = response_json["result"]
    log(f"SUCCESS: {result}")
    return result


def get_nonce():
    return str(int(1000000 * time.time()))


to_kraken_symbols = {
    "btc": "xbt",
    "doge": "xdg",
}

from_kraken_symbols = {v: k for k, v in to_kraken_symbols.items()}


class KrakenAccount:
    def __init__(self):
        pass


    def to_kraken_symbol(self, symbol):
        return to_kraken_symbols.get(symbol, symbol).upper()


    def from_kraken_symbol(self, symbol):
        return from_kraken_symbols.get(symbol.lower(), symbol)


    def get_portfolio(self):
        url_path = "/0/private/Balance"
        data = {"nonce": get_nonce()}
        
        result = handle_request(url_path, data)
        return result


    def get_eur_balance(self):
        url_path = "/0/private/Balance"
        data = {"nonce": get_nonce()}
        
        result = handle_request(url_path, data)
        if result is None:
            return None
        eur_balance = round(float(result["ZEUR"]), 2)
        return eur_balance


    def get_portfolio_value(self):
        url_path = "/0/private/TradeBalance"
        data = {
            "nonce": get_nonce(),
            "asset": "ZEUR",
        }
        
        result = handle_request(url_path, data)
        if result is None:
            return None
        eur_balance = round(float(result["eb"]), 2)
        return eur_balance


    def buy(self, currency_symbol, amount_in_eur):
        url_path = "/0/private/AddOrder"
        data = {
            "nonce": get_nonce(),
            "pair": f"{self.to_kraken_symbol(currency_symbol)}EUR",
            "type": "buy",
            "ordertype": "market",
            "oflags": "viqc",
            "volume": amount_in_eur,
        }

        result = handle_request(url_path, data)
        return result


    def sell(self, currency_symbol, volume):
        url_path = "/0/private/AddOrder"
        data = {
            "nonce": get_nonce(),
            "pair": f"{self.to_kraken_symbol(currency_symbol)}EUR",
            "type": "sell",
            "ordertype": "market",
            "volume": volume,
        }

        result = handle_request(url_path, data)
        return result
