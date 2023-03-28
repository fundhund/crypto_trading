from classes.market_observer import MarketObserver
import time
from datetime import datetime
import pprint

def get_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    return formatted_time

market_observer = MarketObserver()

while True:
    print(get_timestamp())
    pprint.pprint(market_observer.update())
    pprint.pprint(market_observer.candidates)
    pprint.pprint(market_observer.price_trends)
    print("---")

    time.sleep(60)
