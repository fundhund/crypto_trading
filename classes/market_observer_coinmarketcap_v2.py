import requests
import json
import time
import pprint
from classes.log_helper import log


with open("kraken_currencies.json", "r") as f:
    available_on_kraken = json.load(f)

with open("keys/coinmarketcap.txt", "r") as f:
    api_key = f.readline()


parameters = {
    'start':'1',
    'limit':'400',
    'convert':'EUR'
}

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    "Cache-Control": "no-cache",
}

def filter_keys(currency_data):
    new_currency_data = {}
    try:
        numbers = currency_data.get("quote").get("EUR")
        new_currency_data = {
            "name": currency_data.get("name"),
            "symbol": currency_data.get("symbol"),
            "price": numbers.get("price"),
            "change_1h": numbers.get("percent_change_1h"),
            "change_24h": numbers.get("percent_change_24h"),
            "change_7d": numbers.get("percent_change_7d"),
        }
    except:
        log("ERROR: Filtered keys for", currency_data)
    return new_currency_data


class MarketObserver:
    def __init__(self):
        self._candidates = []
        self._prices = {key: [] for key in available_on_kraken}
        self._current_currency = None
        self._market_data = []


    @property
    def current_currency(self):
        """Get current currency."""
        return self._current_currency


    @current_currency.setter
    def current_currency(self, value):
        self._current_currency = value


    @property
    def market_data(self):
        """Get current market data."""
        return self._market_data


    @market_data.setter
    def market_data(self, value):
        self._market_data = value


    @property
    def candidates(self):
        """Get current candidates."""
        return self._candidates


    @candidates.setter
    def candidates(self, value):
        self._candidates = value


    @property
    def prices(self):
        """Get prices."""
        return self._prices


    @prices.setter
    def prices(self, value):
        self._prices = value


    def is_available_on_kraken(self, currency_symbol):
        return currency_symbol.upper() in available_on_kraken


    def is_candidate(self, currency_data):
        if currency_data["symbol"] == self.current_currency:
            return True
    
        change_10m = currency_data["change_10m"]
        change_20m = currency_data["change_20m"]
        change_30m = currency_data["change_30m"]

        if change_10m is None or change_20m is None or change_30m is None: 
            return False

        return change_10m > 0.3 and change_20m > change_10m and change_30m > change_20m


    def is_currently_stable(self, currency_data):
        currency_symbol = currency_data["symbol"]

        if not currency_symbol in self.prices:
            return False
        
        if currency_data.get("change_10m", 0) <= 0 and currency_data.get("change_1h", 0) <= 0:
            return False
        
        return True


    def is_in_candidates(self, currency_symbol):
        return currency_symbol in list(map(lambda x:x["symbol"], self.candidates))


    def get_change_minutes(self, currency_symbol, minutes):
        last_price_index_offset = 1 + minutes//10
        currency_prices = self.prices[currency_symbol]
        if len(currency_prices) < last_price_index_offset:
            return 0
        
        current_price = float(currency_prices[-1])
        last_price = float(currency_prices[-last_price_index_offset])

        return ((current_price - last_price)/last_price) * 100


    def add_short_term_changes_to_market_data(self, currency_symbol):
        for currency_data in self.market_data:
            if currency_data["symbol"] == currency_symbol:
                currency_data['change_10m'] = self.get_change_minutes(currency_symbol, 10)
                currency_data['change_20m'] = self.get_change_minutes(currency_symbol, 20)
                currency_data['change_30m'] = self.get_change_minutes(currency_symbol, 30)
                break


    def update_prices(self):
        for currency_data in self.market_data:
            currency_symbol = currency_data["symbol"]
            self.prices[currency_symbol].append(currency_data["price"])

            self.add_short_term_changes_to_market_data(currency_symbol)

            if len(self.prices[currency_symbol]) >= 6:
                self.prices[currency_symbol] = self.prices[currency_symbol][-6:]


    def update(self):
        response = requests.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                        headers=headers,
                        params=parameters)
        
        if not response.ok:
            log(f"ERROR: Request failed with status code {response.status_code}. Keeping last known candidates.")
            response.close()
            return (None, None)
        
        response_json = response.json()["data"]
        if isinstance(response_json, list):

            self.market_data = list(map(filter_keys, filter(lambda x:self.is_available_on_kraken(x["symbol"]), response_json)))
            response.close()
        
        current_currency_data = next((currency_data for currency_data in self.market_data if currency_data["symbol"] == self.current_currency), None)
        
        self.update_prices()
        self.candidates = list(sorted(filter(self.is_candidate, self.market_data), key=lambda x:x["change_10m"] if x["change_10m"] else 0, reverse=True))
        
        top_currency_data = self.candidates[0] if self.candidates else None

        return (current_currency_data, top_currency_data)
