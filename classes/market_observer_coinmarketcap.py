import requests
import json
import time
import pprint


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
        print("Error: ", currency_data)
    return new_currency_data


class MarketObserver:
    def __init__(self):
        self._candidates = []
        self._price_trends = {}
        self._current_currency = {
            "symbol": None,
            "purchase_price": None,
        }


    @property
    def current_currency(self):
        """Get current candidates."""
        return self._current_currency


    @current_currency.setter
    def current_currency(self, value):
        self._current_currency = value

    def update_current_currency(self, currency_data):
        self.current_currency = {
            "symbol": currency_data["symbol"],
            "purchase_price": currency_data["price"],
        }


    @property
    def candidates(self):
        """Get current candidates."""
        return self._candidates


    @candidates.setter
    def candidates(self, value):
        self._candidates = value


    @property
    def price_trends(self):
        """Get current price trends."""
        return self._price_trends


    @price_trends.setter
    def price_trends(self, value):
        self._price_trends = value


    def is_candidate(self, currency_data):
        if currency_data["symbol"] == self.current_currency["symbol"]:
            return True
    
        change_1h = currency_data["change_1h"]
        change_24h = currency_data["change_24h"]

        if change_1h is None or change_24h is None:
            return False

        has_positive_trend = change_1h > 0.5 and change_24h >= change_1h
        is_available_on_kraken = currency_data["symbol"].upper() in available_on_kraken

        return has_positive_trend and is_available_on_kraken


    def is_currently_stable(self, currency_data):
        currency_symbol = currency_data["symbol"]

        if not currency_symbol in self.price_trends:
            return False
        
        price_trend = self.price_trends[currency_symbol]

        if len(price_trend) >= 2 and price_trend[-1] < price_trend[-2]:
            return False
        
        return True


    def is_in_candidates(self, currency_symbol):
        return currency_symbol in list(map(lambda x:x["symbol"], self.candidates))


    def update_price_trends(self, new_candidates = []):
        for candidate in new_candidates:
            candidate_symbol = candidate["symbol"]
            if candidate_symbol in self.price_trends:
                self.price_trends[candidate_symbol].append(candidate["price"])
                if len(self.price_trends[candidate_symbol]) >= 6:
                    self.price_trends[candidate_symbol] = self.price_trends[candidate_symbol][-6:]
            else:
                self.price_trends[candidate_symbol] = [candidate["price"]]
        
        old_candidates_to_delete = []
        
        for candidate_symbol in self.price_trends:
            if candidate_symbol not in map(lambda x:x["symbol"], new_candidates):
                old_candidates_to_delete.append(candidate_symbol)

        for candidate_symbol in old_candidates_to_delete:
            self.price_trends.pop(candidate_symbol)


    def update(self):
        new_candidates = []

        response = requests.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                        headers=headers,
                        params=parameters)
        
        if not response.ok:
            print(f"Error: Request failed with status code {response.status_code}. Keeping last known candidates.")
            response.close()
            return (None, None)
        
        response_json = response.json()["data"]
        if isinstance(response_json, list):

            new_candidates = list(filter(self.is_candidate, map(filter_keys, response_json)))
            response.close()
        
        current_currency_data = next((currency_data for currency_data in new_candidates if currency_data["symbol"] == self.current_currency["symbol"]), None)
        
        self.update_price_trends(new_candidates)
        pprint.pprint(self.price_trends)
        self.candidates = list(sorted(filter(self.is_currently_stable, new_candidates), key=lambda x:x["change_1h"] if x["change_1h"] else 0, reverse=True))
        
        top_currency_data = self.candidates[0] if self.candidates else None

        return (current_currency_data, top_currency_data)
