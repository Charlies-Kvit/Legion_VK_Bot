import datetime
from config import HOUR, MINUTES, WARNING_HOUR, WARNING_MINUTES


def check_time():
    return datetime.datetime.now().hour == HOUR and MINUTES - 4 <= datetime.datetime.now().minute <= MINUTES


def check_warning_time():
    return datetime.datetime.now().hour == WARNING_HOUR and WARNING_MINUTES - 5 <= datetime.datetime.now().minute <= WARNING_MINUTES


def change_loyalty(loyalty, user_loyalty):
    if loyalty[0] == "+":
        return int(int(user_loyalty) + int(loyalty[1:]))
    elif loyalty[0] == "-":
        return int(int(user_loyalty) - int(loyalty[1:]))
    else:
        return "error"
