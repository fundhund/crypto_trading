from classes.market_observer import MarketObserver
import time
from datetime import datetime

market_observer = MarketObserver()

while True:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    print(formatted_time)

    market_observer.update_candidates()
    print(market_observer.candidates)
    print(market_observer.price_trends)
    print("---")

    time.sleep(60)
