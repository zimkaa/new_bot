import os
from decimal import Decimal

from dotenv import load_dotenv


load_dotenv()

DB_NAME = os.getenv("DB_NAME")

TOKEN = os.getenv("TOKEN")

KEY = os.getenv("KEY")

SECRET = os.getenv("SECRET")

RISE_UP_TO = os.getenv("RISE_UP_TO")

DOWN_TO = os.getenv("DOWN_TO")

STOP_LOSS = os.getenv("STOP_LOSS")

PERCENTAGE_COMMISSION = Decimal(os.getenv("PERCENTAGE_COMMISSION"))

COEFFICIENT_FOR_PROFIT = 1 + (PERCENTAGE_COMMISSION * 2 + PERCENTAGE_COMMISSION * 2 / 10) / 100

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


TRIGGER_PRICE_FALL_PER_MINUTE = Decimal(os.getenv("TRIGGER_PRICE_FALL_PER_MINUTE"))


if __name__ == "__main__":
    print(COEFFICIENT_FOR_PROFIT)
