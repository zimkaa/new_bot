import argparse
import os
import sys
from decimal import Decimal

from dotenv import load_dotenv


load_dotenv()


# создаём парсер аргументов и передаём их
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--db-name", help="path to input database")
# ap.add_argument("-t", "--test", help="run with test mode. it means 'trades operation will not execute'")
args = vars(ap.parse_args())


# if sys.version_info >= (3, 10):
#     from typing import TypeAlias  # it's for 3.10 Python

#     not_negative_float: TypeAlias = confloat(strict=True, ge=0.0)  # it's for 3.10 Python
# else:
#     not_negative_float = confloat(strict=True, ge=0.0)  # it's for 3.8 Python

# if db_path := args["db_name"]:  # it's for 3.10 Python
if args["db_name"]:  # it's for 3.8 Python
    db_path = args["db_name"]
    # DB_NAME = os.getenv("DB_NAME", "files/my.db")
    # DB_NAME = os.getenv("DB_NAME", db_path)
    DB_NAME = db_path
else:
    DB_NAME = os.getenv("DB_NAME", "files/my_simple.db")
    # DB_NAME = os.getenv("DB_NAME", "files/my.db")

# DB_NAME = os.getenv("DB_NAME", "files/my.db")
# DB_NAME = os.getenv("DB_NAME", "files/my_simple.db")

print(f"{DB_NAME=}")
# DB_NAME_SIMPLE = os.getenv("DB_NAME_SIMPLE", "files/my_simple.db")

STATE_FILE = os.getenv("STATE_FILE", "state.json")
STATE_FILE_TEST = os.getenv("STATE_FILE_TEST", "state_test.json")
STATE_FILE_SIMPLE = os.getenv("STATE_FILE_SIMPLE", "state_simple.json")

STORAGE_FILE = os.getenv("STORAGE_FILE", "storage.json")
STORAGE_FILE_TEST = os.getenv("STORAGE_FILE_TEST", "storage_test.json")
STORAGE_FILE_SIMPLE = os.getenv("STORAGE_FILE_SIMPLE", "storage_simple.json")

SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.json")
# STORAGE_FILE_TEST = os.getenv("STORAGE_FILE_TEST", "storage_test.json")
# STORAGE_FILE_SIMPLE = os.getenv("STORAGE_FILE_SIMPLE", "storage_simple.json")

TOKEN = os.getenv("TOKEN")

# KEY = os.getenv("KEY")
KEY = os.getenv("BINANCE_KEY")

# SECRET = os.getenv("SECRET")
SECRET = os.getenv("BINANCE_SECRET")

TRADE = os.getenv("TRADE", "ON")
# TRADE = os.getenv("TRADE", "OFF")

# TEST = True
TEST = False

# 1 - first strategy
# 2 - new strategy byt and sell when + 1%
STRATEGY = os.getenv("STRATEGY", 1)

TIME_FORMAT = os.getenv("TIME_FORMAT", "%Y-%m-%d %H:%M:%S")

PERCENTAGE_RISE_UP_TO = Decimal(os.getenv("PERCENTAGE_RISE_UP_TO", 0.5))

PERCENTAGE_DOWN_TO = Decimal(os.getenv("PERCENTAGE_DOWN_TO", 0.5))

PERCENTAGE_STOP_LOSS = Decimal(os.getenv("PERCENTAGE_STOP_LOSS", 1))

PERCENTAGE_WAIT_AFTER_SELL = Decimal(os.getenv("PERCENTAGE_WAIT_AFTER_SELL", 1))

PERCENTAGE_WAIT_FOR_BUY = Decimal(os.getenv("PERCENTAGE_WAIT_FOR_BUY", 0.1))

PERCENTAGE_COMMISSION = Decimal(os.getenv("PERCENTAGE_COMMISSION", 0.075))

PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE = Decimal(os.getenv("PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE", 0.2))

PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY = Decimal(
    os.getenv("PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY", 0.2)
)

PERCENTAGE_TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY = Decimal(
    os.getenv("PERCENTAGE_TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY", 1.5)
)

ROUNDING = os.getenv("ROUNDING", ".00001")
