from classes.market_observer_coinmarketcap import MarketObserver
from classes.kraken_account import KrakenAccount
from classes.log_helper import log, get_timestamp
import time
from datetime import datetime
# import pprint


last_purchase_time = None
is_first_iteration = True
estimated_fee_share = 0.005
update_interval = 600
swap_cooldown = 1800
min_diff_for_swap = 1 # Increase to  2?

market_observer = MarketObserver()
kraken_account = KrakenAccount()


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
    
    kraken_symbol = kraken_account.to_kraken_symbol(currency_symbol)
    volume = portfolio[f"X{kraken_symbol}"]
    return volume


def sell_all(currency_symbol):
    log(f"ACTION: Selling {currency_symbol.upper()}")
    volume = get_currency_volume(currency_symbol)
    kraken_account.sell(currency_symbol, volume)
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


while True:
    if is_first_iteration:
        is_first_iteration = False
    else:
        log("\n")
        time.sleep(update_interval)

    log(f"{get_timestamp()}\n")

    kraken_account.get_portfolio()
    kraken_account.get_portfolio_value()

    current_currency_symbol = market_observer.current_currency
    current_currency_data, top_currency_data = market_observer.update()

    print_candidates(market_observer.candidates)

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
            and ((top_currency_data["change_1h"] - current_currency_data["change_1h"]) > min_diff_for_swap)
            and is_swap_cooldown_over()
        ):
            log(f"EVENT {current_currency_symbol.upper()} ({current_currency_data['change_1h']} %) significantly surpassed by {top_currency_data['symbol'].upper()} ({top_currency_data['change_1h']} %)")
            swap_currencies(current_currency_symbol, top_currency_data["symbol"])
            continue

        # If current coin is falling, get rid of it.
        elif current_currency_data["change_1h"] <= 0:
            log(f"EVENT: {current_currency_symbol} is making losses in the last hour ({current_currency_data['change_1h'] } %)")
            last_purchase_time = None
            if top_currency_data is not None:
                swap_currencies(current_currency_data, top_currency_data["symbol"])
                continue
            else:
                log("EVENT: No candidates")
                sell_all(current_currency_symbol)
                continue

        else:
            log(f"EVENT: Keeping {current_currency_symbol.upper()} at {current_currency_data['change_1h']} %")
            continue
