from classes.market_observer_coinmarketcap import MarketObserver
from classes.kraken_account import KrakenAccount
import time
from datetime import datetime
import pprint


last_purchase_time = None
is_first_iteration = True
estimated_fee_share = 0.005
update_interval = 60
swap_cooldown = 180
min_diff_for_swap = 1

market_observer = MarketObserver()
kraken_account = KrakenAccount()


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


def buy(currency_symbol, share_of_balance=1):
    log(f"Buying {currency_symbol.upper()} for {str(share_of_balance * 100)} % of available EUR...")
    global last_purchase_time
    eur_balance = kraken_account.get_eur_balance()
    if eur_balance is not None and eur_balance > 0:
        available_funds = eur_balance * share_of_balance * (1 - estimated_fee_share)
        kraken_account.buy(currency_symbol, available_funds)
        market_observer.update_current_currency(top_currency_data)
        last_purchase_time = datetime.now()


def sell_all(currency_symbol):
    log(f"Selling all {currency_symbol.upper()} for EUR...")
    kraken_account.sell_all(currency_symbol)
    if market_observer.current_currency["symbol"] == currency_symbol:
        market_observer.update_current_currency({
            "symbol": None,
            "purchase_price": None,
        })


def swap_currencies(old, new):
    log(f"Swapping {old.upper()} for {new.upper()}...")
    buy(new)
    sell_all(old)


def is_swap_cooldown_over():
    if last_purchase_time is None:
        return True
    return (datetime.now() - last_purchase_time).total_seconds() >= swap_cooldown

def log(text):
    filename = "logs/" + datetime.today().strftime('%Y-%m-%d')
    with open(filename, "a") as f:
        f.write(text + "\n")
    print(text)

while True:
    if is_first_iteration:
        is_first_iteration = False
    else:
        time.sleep(60)

    log(f"------------------------------\n{get_timestamp()}\n------------------------------")

    current_currency_symbol = market_observer.current_currency["symbol"]
    current_currency_data, top_currency_data = market_observer.update()

    print_candidates(market_observer.candidates)

    # pprint.pprint(current_currency_data)
    # pprint.pprint(top_currency_data)

    if current_currency_symbol is None:
        log(f"No coin in portfolio yet...")

        # If no crypto in prtfoio, use 50 % of EUR balance (minus estimated transaction fee) to buy best coin.
        if top_currency_data is not None:
            buy(top_currency_data["symbol"], 0.5)
            continue

        # If no crypto in portfolio and no candidates, do nothing.
        else:
            print("...and no candidates. Nothing to do.")
            continue

    else:

        # If current coin gets surpassed by more than min_diff_for_swap %, swap.
        if (
            top_currency_data is not None
            and ((top_currency_data["change_1h"] - current_currency_data["change_1h"]) > min_diff_for_swap)
            and is_swap_cooldown_over()
        ):
            log(f"{current_currency_symbol.upper()} ({current_currency_data['change_1h']} %) surpassed by {top_currency_data['symbol'].upper()} ({top_currency_data['change_1h']} %).")
            swap_currencies(current_currency_symbol, top_currency_data["symbol"])
            continue

        
        elif current_currency_data["change_1h"] <= 0:
            log(f"{current_currency_symbol} is making losses ({current_currency_data['change_1h'] } %). Time to get rid of it...")
            if top_currency_data is not None:
                log(f"{top_currency_data['symbol'].upper()} looks better.")
                swap_currencies(current_currency_data, top_currency_data["symbol"])
                continue
            else:
                log("Nothing else to buy right now...")
                sell_all(current_currency_symbol)
                continue

        else:
            log(f"All good. {current_currency_symbol.upper()} still strong at {current_currency_data['change_1h']} %.")
            continue
