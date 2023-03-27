import requests
import time
from datetime import datetime
import json

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

current_currency = None
# to do: save 1h change if currency remains trhe same.

def get_api_url(page):
    api_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&order=market_cap_desc&per_page=250&page={page}&sparkline=false&price_change_percentage=1h%2C24h%2C7d&randInt={str(int(time.time()*1000))}"
    return api_url

def filter_keys(currency):
    new_dict = {}
    try:
        new_dict = {key: currency[key] for key in relevant_keys}
    except:
        print("Error: ", currency)
    return new_dict

def is_candidate(currency):
    change_1h = currency["price_change_percentage_1h_in_currency"]
    change_24h = currency["price_change_percentage_24h_in_currency"]
    change_7d = currency["price_change_percentage_7d_in_currency"]

    if change_1h is None or change_24h is None or change_7d is None:
        return False
    
    is_available_on_kraken = currency["symbol"].upper() in available_on_kraken
    return change_1h > 0 and change_24h >= change_1h and change_7d >= change_24h and is_available_on_kraken

def get_best_available_currency():
    response1 = requests.get(get_api_url(1), headers={"Cache-Control": "no-cache"})
    print(response1)
    print(response1.ok)
    print(response1.status_code)
    response1 = response1.json()
    response2 = requests.get(get_api_url(2), headers={"Cache-Control": "no-cache"}).json()
    response3 = requests.get(get_api_url(3), headers={"Cache-Control": "no-cache"}).json()
    response4 = requests.get(get_api_url(4), headers={"Cache-Control": "no-cache"}).json()

    response = []
    if isinstance(response1, list):
        response += response1
    if isinstance(response2, list):
        response += response2
    if isinstance(response3, list):
        response += response3
    if isinstance(response4, list):
        response += response4

    sorted_currencies = list(filter(is_candidate, map(filter_keys, response)))
    sorted_currencies.sort(key=lambda x:x["price_change_percentage_1h_in_currency"] if x["price_change_percentage_1h_in_currency"] else 0, reverse=True)
    if len(sorted_currencies) > 0:
        return sorted_currencies[0]
    else:
        return None
    
def get_candidates(per_page=250, pages=4):
    candidates = []
    for page in range(1, pages + 1):
        api_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&order=market_cap_desc&per_page={per_page}&page={page}&sparkline=false&price_change_percentage=1h%2C24h%2C7d&randInt={str(int(time.time()*1000))}"
        response = requests.get(api_url, headers={"Cache-Control": "no-cache"})
        print(response)
        if not response.ok:
            continue
        response_json = response.json()
        if isinstance(response_json, list):
            candidates += list(filter(is_candidate, map(filter_keys, response_json)))
    candidates.sort(key=lambda x:x["price_change_percentage_1h_in_currency"] if x["price_change_percentage_1h_in_currency"] else 0, reverse=True)
    return candidates


candidate_trends = {}


def update_candidate_trends(new_candidates = []):
    global candidate_trends
    for candidate in new_candidates:
        candidate_symbol = candidate["symbol"]
        if candidate_symbol in candidate_trends:
            candidate_trends[candidate_symbol].append(candidate["current_price"])
        else:
            candidate_trends[candidate_symbol] = [candidate["current_price"]]
    
    old_candidates_to_delete = []
    
    for candidate_symbol in candidate_trends:
        if candidate_symbol not in map(lambda x:x["symbol"], new_candidates):
            old_candidates_to_delete.append(candidate_symbol)

    for candidate_symbol in old_candidates_to_delete:
        candidate_trends.pop(candidate_symbol)


def print_candidates_trends():
    for currency, trend in candidate_trends.items():
        print(currency, trend, is_sus(currency))
    print("---")

def is_sus(currency):
    if not currency in candidate_trends:
        return True
    
    trend = candidate_trends[currency]

    if len(trend) >= 15 and trend[14] < trend[0]:
        return True
    
    for i in range(1, len(trend)):
        if trend[i] <= (trend[i - 1] * 0.99):
            return True
        
    return False


while True:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    best_currency = get_best_available_currency()
    if best_currency == None:
        print("no currency available")
    else:
        print(formatted_time, best_currency["name"], best_currency["price_change_percentage_1h_in_currency"], best_currency["price_change_percentage_24h_in_currency"], best_currency["price_change_percentage_7d_in_currency"])
    print('---')
    time.sleep(60)

# print(requests.get(get_api_url(1), headers={"Cache-Control": "no-cache"}).ok)
# print(list(range(1, 5)))

# while True: 
#     current_time = datetime.now()
#     formatted_time = current_time.strftime("%H:%M:%S")
#     print(formatted_time)
#     candidates = get_candidates(pages=1, per_page=100)
#     update_candidate_trends(candidates)
#     print_candidates_trends()
#     time.sleep(60)

