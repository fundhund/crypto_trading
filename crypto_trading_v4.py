from classes.market_observer_coinmarketcap_v4 import MarketObserver
from classes.kraken_account import KrakenAccount
from classes.log_helper import log, get_timestamp
import time
from datetime import datetime
import sys

args = sys.argv

last_purchase_time = None
is_first_iteration = True
estimated_fee_share = 0.005
update_interval = 300
swap_cooldown = 3600
min_diff_for_swap = 2

market_observer = MarketObserver(args[1]) if len(args) > 1 else MarketObserver()
kraken_account = KrakenAccount()


def print_candidates():
    print("\nCANDIDATES\n")

    if not market_observer.candidates:
        print("No candidates.")
    else:
        max_len_names = max(map(lambda x:len(x["name"]), market_observer.candidates))
        max_len_symbols = max(map(lambda x:len(x["symbol"]), market_observer.candidates))
        for count, candidate in enumerate(market_observer.candidates):
            pos = (str(count + 1) + '.').rjust(3)
            name = candidate['name'].ljust(max_len_names)
            symbol = candidate['symbol'].upper().ljust(max_len_symbols)
            c_10m = str(round(candidate['change_5m'], 2)).rjust(4)
            c_20m = str(round(candidate['change_10m'], 2)).rjust(4)
            c_30m = str(round(candidate['change_15m'], 2)).rjust(4)
            c_1h = str(round(candidate['change_1h'], 2)).rjust(4)
            c_24h = str(round(candidate['change_24h'], 2)).rjust(4)
            c_7d = str(round(candidate['change_7d'], 2)).rjust(4)
            print(pos, name, symbol, c_10m, c_20m, c_30m, c_1h, c_24h, c_7d)
    print("\n")


def buy(currency_symbol, share_of_balance=1):
    log(f"ACTION: Buying {currency_symbol.upper()} using {str(share_of_balance * 100)} % of available funds")
    global last_purchase_time
    eur_balance = kraken_account.get_eur_balance()
    if eur_balance is not None and eur_balance > 0:
        available_funds = round(eur_balance * share_of_balance * (1 - estimated_fee_share), 2)
        kraken_account.buy(currency_symbol, available_funds)
        market_observer.current_currency = currency_symbol
        last_purchase_time = datetime.now()


def get_currency_volume(currency_symbol):
    portfolio = kraken_account.get_portfolio()
    
    if portfolio is None:
        return None
    
    kraken_symbol = kraken_account.to_kraken_symbol(currency_symbol.lower())
    if kraken_symbol in portfolio:
        return portfolio[f"{kraken_symbol}"]
    elif f"X{kraken_symbol}" in portfolio:
        return portfolio[f"X{kraken_symbol}"]
    else:
        return 0


def sell_all(currency_symbol):
    log(f"ACTION: Selling {currency_symbol.upper()}")
    volume = get_currency_volume(currency_symbol)
    print(volume)
    kraken_account.sell(currency_symbol, volume)
    if market_observer.current_currency == currency_symbol:
        market_observer.current_currency = None


def swap_currencies(old, new):
    log(f"Swapping {old.upper()} for {new.upper()}...")
    buy(new)
    sell_all(old)


def is_swap_cooldown_over():
    if last_purchase_time is None:
        return True
    return (datetime.now() - last_purchase_time).total_seconds() >= swap_cooldown


while True:
    if is_first_iteration:
        is_first_iteration = False
    else:
        log("\n")
        time.sleep(update_interval)

    log(f"{get_timestamp()}\n")

    current_currency_symbol = market_observer.current_currency
    current_currency_data, top_currency_data = market_observer.update()

    print_candidates()

    if current_currency_symbol is None:
        log("EVENT: No coin in portfolio yet")

        # If no crypto in prtfoio, use 50 % of EUR balance (minus estimated transaction fee) to buy best coin.
        if top_currency_data is not None:
            buy(top_currency_data["symbol"], 0.5)
            continue

        # If no crypto in portfolio and no candidates, do nothing.
        else:
            log("EVENT: No candidates")
            continue

    else:
        # If current coin gets surpassed by more than min_diff_for_swap %, swap.
        if (
            top_currency_data is not None
            and ((top_currency_data["change_5m"] - current_currency_data["change_5m"]) > min_diff_for_swap)
            and is_swap_cooldown_over()
        ):
            log(f"EVENT {current_currency_symbol.upper()} ({current_currency_data['change_5m']} %) significantly surpassed by {top_currency_data['symbol'].upper()} ({top_currency_data['change_5m']} %)")
            swap_currencies(current_currency_symbol, top_currency_data["symbol"])
            continue

        # If current coin is falling, get rid of it.
        elif current_currency_data["change_10m"] is not None and current_currency_data["change_10m"] < 0:
            log(f"EVENT: {current_currency_symbol} is making losses ({current_currency_data['change_10m']} % in 10 min)")
            last_purchase_time = None
            if top_currency_data is not None and current_currency_data["symbol"] != top_currency_data["symbol"]:
                swap_currencies(current_currency_data["symbol"], top_currency_data["symbol"])
                continue
            else:
                log("EVENT: No candidates")
                sell_all(current_currency_symbol)
                continue

        else:
            log(f"ACTION: Keeping {current_currency_symbol.upper()} at {current_currency_data['change_5m']} %")
            continue
