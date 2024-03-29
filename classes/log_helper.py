from datetime import datetime

def get_timestamp():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    return formatted_time


def log(text):
    filename = f"logs/{datetime.today().strftime('%Y-%m-%d')}.txt"
    with open(filename, "a") as f:
        f.write(text + "\n")
    print(text)

