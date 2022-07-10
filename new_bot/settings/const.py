from .main_settings import PERCENTAGE_COMMISSION
from .main_settings import PERCENTAGE_DOWN_TO
from .main_settings import PERCENTAGE_RISE_UP_TO
from .main_settings import PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE
from .main_settings import PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY
from .main_settings import PERCENTAGE_WAIT_AFTER_SELL
from .main_settings import PERCENTAGE_WAIT_FOR_BUY
from .main_settings import TRADE
from .main_settings import PERCENTAGE_STOP_LOSS
from .main_settings import TEST


COEFFICIENT_RISE_UP_TO = 1 + PERCENTAGE_RISE_UP_TO / 100

COEFFICIENT_FOR_PROFIT = 1 + (PERCENTAGE_COMMISSION * 2 + PERCENTAGE_COMMISSION * 2 / 10) / 100

TRIGGER_PRICE_FALL_PER_MINUTE = PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE / 100

TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY = PERCENTAGE_TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY / 100

COEFFICIENT_DOWN_TO = 1 - PERCENTAGE_DOWN_TO / 100

COEFFICIENT_WAIT_AFTER_SELL = 1 - PERCENTAGE_WAIT_AFTER_SELL / 100

COEFFICIENT_WAIT_FOR_BUY = PERCENTAGE_WAIT_FOR_BUY / 100

STOP_LOSS_RATIO = 1 - PERCENTAGE_STOP_LOSS / 100

trade_list = ["ON", "On", "on", "True", "true", "YES", "Yes", "yes"]

if TRADE in trade_list:
    ONLINE_TRADE = True
else:
    ONLINE_TRADE = False

if TEST:
    ONLINE_TRADE = False
