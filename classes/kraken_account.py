to_kraken_symbols = {
    "btc": "xbt",
}

from_kraken_symbols = {v: k for k, v in to_kraken_symbols.items()}

def to_kraken_symbol(symbol):
    return to_kraken_symbols.get(symbol, symbol).upper()

def from_kraken_symbol(symbol):
    return from_kraken_symbols.get(symbol.lower(), symbol)

class KrakenAccount:
    def __init__(self):
        # Create API header, secret and stuff
        pass

    # todo
    def get_eur_balance(self):
        return 250

    # todo
    def buy(self, currency_symbol, amount_in_eur):
        print(f"Buying {to_kraken_symbol(currency_symbol)} for {amount_in_eur} EUR...")

    # todo
    def sell_all(self, currency_symbol):
        print(f"Selling all our {to_kraken_symbol(currency_symbol)}...")
