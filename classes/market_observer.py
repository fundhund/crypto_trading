import requests
import json
import time

with open('kraken_currencies.json') as f:
    available_on_kraken = json.load(f)

relevant_keys = [
    "name",
    "symbol",
    "current_price",
    "price_change_percentage_1h_in_currency",
    "price_change_percentage_24h_in_currency",
    "price_change_percentage_7d_in_currency",
]


def filter_keys(currency_data):
    new_dict = {}
    try:
        new_dict = {key: currency_data[key] for key in relevant_keys}
    except:
        print("Error: ", currency_data)
    return new_dict


def is_candidate(currency_data):

    if (
        "price_change_percentage_1h_in_currency" not in currency_data
        or "price_change_percentage_24h_in_currency" not in currency_data
        or "price_change_percentage_7d_in_currency" not in currency_data   
    ):
        return False
    
    change_1h = currency_data["price_change_percentage_1h_in_currency"]
    change_24h = currency_data["price_change_percentage_24h_in_currency"]
    change_7d = currency_data["price_change_percentage_7d_in_currency"]

    if change_1h is None or change_24h is None or change_7d is None:
        return False

    has_positive_trend = change_1h > 0 and change_24h >= change_1h and change_7d >= change_24h
    is_available_on_kraken = currency_data["symbol"].upper() in available_on_kraken

    return has_positive_trend and is_available_on_kraken


class MarketObserver:
    def __init__(self):
        self.candidates = []
        self.price_price_trends = {}


    def is_falling_fast(self, currency):
        if not currency in self.price_price_trends:
            return True
        
        price_trend = self.price_price_trends[currency]

        if len(price_trend) >= 15 and price_trend[-1] < price_trend[0]:
            return True
        
        if len(price_trend) >= 5 and price_trend[-1] <= (price_trend[-5] * 0.99):
            return True
        
        return False


    def is_in_candidates(self, currency_symbol):
        return currency_symbol in list(map(lambda x:x["symbol"], self.candidates))


    def get_candidates(self, per_page=250, pages=4):
        candidates = []
        
        for page in range(1, pages + 1):
            api_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&order=market_cap_desc&per_page={per_page}&page={page}&sparkline=false&price_change_percentage=1h%2C24h%2C7d&randInt={str(int(time.time()*1000))}"
            response = requests.get(api_url, headers={"Cache-Control": "no-cache"})
            if not response.ok:
                print(f"Request failed with status code {response.status_code}. Returning last known candidates.")
                return self.candidates
            response_json = response.json()
            if isinstance(response_json, list):
                candidates += list(filter(is_candidate, map(filter_keys, response_json)))
            response.close()
        
        candidates.sort(key=lambda x:x["price_change_percentage_1h_in_currency"] if x["price_change_percentage_1h_in_currency"] else 0, reverse=True)
        
        self.candidates = candidates
        return candidates
