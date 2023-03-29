from classes.market_observer_coinmarketcap import MarketObserver
from classes.kraken_account import KrakenAccount
import time
from datetime import datetime
import pprint

def get_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    return formatted_time


def print_candidates(candidates):
    print("\nCANDIDATES\n")

    if not candidates:
        print("No candidates.")
    else:
        max_len_names = max(map(lambda x:len(x["name"]), candidates))
        max_len_symbols = max(map(lambda x:len(x["symbol"]), candidates))
        for count, candidate in enumerate(candidates):
            pos = (str(count + 1) + '.').rjust(3)
            name = candidate['name'].ljust(max_len_names)
            symbol = candidate['symbol'].upper().ljust(max_len_symbols)
            c_1h = str(round(candidate['change_1h'], 2)).rjust(4)
            c_24h = str(round(candidate['change_24h'], 2)).rjust(4)
            c_7d = str(round(candidate['change_7d'], 2)).rjust(4)
            print(pos, name, symbol, c_1h, c_24h, c_7d)
    print("\n")

market_observer = MarketObserver()
kraken_account = KrakenAccount()

last_purchase_time = None

is_first_iteration = True

while True:
    if is_first_iteration:
        is_first_iteration = False
    else:
        time.sleep(60)

    print(get_timestamp())

    current_currency_symbol = market_observer.current_currency["symbol"]
    current_currency_data, top_currency_data = market_observer.update()

    print_candidates(market_observer.candidates)

    # pprint.pprint(current_currency_data)
    # pprint.pprint(top_currency_data)

    # if current_currency_symbol is None:

    #     if top_currency_data is not None:

    #         # Use 50 % of EUR balance (minus estimated transaction fee) to buy best coin

    #         eur_balance = kraken_account.get_eur_balance()
    #         if eur_balance is not None and eur_balance > 0:
    #             available_funds = eur_balance * 0.5 * 0.995
    #             kraken_account.buy(top_currency_data["symbol"], available_funds)
    #             market_observer.update_current_currency(top_currency_data)
    #             last_purchase_time = datetime.now()
    #             print(market_observer.current_currency)

    #     else:
    #         continue


    # pprint.pprint(market_observer.update())
    # pprint.pprint(market_observer.candidates)
    # pprint.pprint(market_observer.price_trends)
    print("---")

