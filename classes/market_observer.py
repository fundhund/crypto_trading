import requests
import json
import time

with open('kraken_currencies.json') as f:
    available_on_kraken = json.load(f)


def filter_keys(currency_data):
    new_currency_data = {}
    try:
        new_currency_data = {
            "name": currency_data.get("name"),
            "symbol": currency_data.get("symbol"),
            "price": currency_data.get("current_price"),
            "change_1h": currency_data.get("price_change_percentage_1h_in_currency"),
            "change_24h": currency_data.get("price_change_percentage_24h_in_currency"),
            "change_7d": currency_data.get("price_change_percentage_7d_in_currency"),
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

        if len(price_trend) >= 10 and price_trend[-1] < price_trend[0]:
            return False
        
        if len(price_trend) >= 5 and price_trend[-1] <= (price_trend[-5] * 0.99):
            return False
        
        return True


    def is_in_candidates(self, currency_symbol):
        return currency_symbol in list(map(lambda x:x["symbol"], self.candidates))


    def update_price_trends(self, new_candidates = []):
        for candidate in new_candidates:
            candidate_symbol = candidate["symbol"]
            if candidate_symbol in self.price_trends:
                self.price_trends[candidate_symbol].append(candidate["price"])
                if len(self.price_trends[candidate_symbol]) >= 10:
                    self.price_trends[candidate_symbol] = self.price_trends[candidate_symbol][-10:]
            else:
                self.price_trends[candidate_symbol] = [candidate["price"]]
        
        old_candidates_to_delete = []
        
        for candidate_symbol in self.price_trends:
            if candidate_symbol not in map(lambda x:x["symbol"], new_candidates):
                old_candidates_to_delete.append(candidate_symbol)

        for candidate_symbol in old_candidates_to_delete:
            self.price_trends.pop(candidate_symbol)


    def update(self, per_page=250, pages=4):
        new_candidates = []
        
        for page in range(1, pages + 1):
            api_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&order=market_cap_desc&per_page={per_page}&page={page}&sparkline=false&price_change_percentage=1h%2C24h%2C7d&randInt={str(int(time.time()*1000))}"
            response = requests.get(api_url, headers={"Cache-Control": "no-cache"})
            if not response.ok:
                print(f"Error: Request failed with status code {response.status_code}. Keeping last known candidates.")
                return {
                    "current_currency_data": None,
                    "top_currency_data": None,
                }
            response_json = response.json()
            if isinstance(response_json, list):
                new_candidates += list(filter(self.is_candidate, map(filter_keys, response_json)))
            response.close()
        
        current = next((currency_data for currency_data in self.candidates if currency_data["symbol"] == self.current_currency["symbol"]), None)
        
        self.update_price_trends(new_candidates)
        self.candidates = list(sorted(filter(self.is_currently_stable, new_candidates), key=lambda x:x["change_1h"] if x["change_1h"] else 0, reverse=True))
        
        top = self.candidates[0] if self.candidates else None

        return {
            "current_currency_data": current,
            "top_currency_data": top,
        }
