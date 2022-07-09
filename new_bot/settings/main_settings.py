import os
from decimal import Decimal

from dotenv import load_dotenv


load_dotenv()

DB_NAME = os.getenv("DB_NAME", "my.db")

TOKEN = os.getenv("TOKEN")

# KEY = os.getenv("KEY")
KEY = os.getenv("BINANCE_KEY")

# SECRET = os.getenv("SECRET")
SECRET = os.getenv("BINANCE_SECRET")

TRADE = os.getenv("TRADE")

TIME_FORMAT = os.getenv("TIME_FORMAT", "%Y-%m-%d %H:%M:%S")

PERCENTAGE_RISE_UP_TO = Decimal(os.getenv("PERCENTAGE_RISE_UP_TO", 0.5))

PERCENTAGE_DOWN_TO = Decimal(os.getenv("PERCENTAGE_DOWN_TO", 0.3))

PERCENTAGE_STOP_LOSS = Decimal(os.getenv("PERCENTAGE_STOP_LOSS", 1))

PERCENTAGE_WAIT_AFTER_SELL = Decimal(os.getenv("PERCENTAGE_WAIT_AFTER_SELL", 1))

PERCENTAGE_WAIT_FOR_BUY = Decimal(os.getenv("PERCENTAGE_WAIT_FOR_BUY", 0.1))

PERCENTAGE_COMMISSION = Decimal(os.getenv("PERCENTAGE_COMMISSION", 0.075))

PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE = Decimal(os.getenv("PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE", 0.2))

PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY = Decimal(
    os.getenv("PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY", 0.2)
)

ROUNDING = os.getenv("ROUNDING", ".00001")
