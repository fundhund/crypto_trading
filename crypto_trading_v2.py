from classes.market_observer import MarketObserver
import time

market_observer = MarketObserver()

while True:
    print(market_observer.get_candidates())
    time.sleep(60)
