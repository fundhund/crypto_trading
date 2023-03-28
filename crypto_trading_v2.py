from classes.market_observer import MarketObserver
import time
from datetime import datetime

def get_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    return formatted_time

market_observer = MarketObserver()

while True:
    print(get_timestamp())
    print(market_observer.update())
    print(market_observer.candidates)
    print(market_observer.price_trends)
    print("---")

    time.sleep(60)
