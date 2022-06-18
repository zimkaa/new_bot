from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN

from loguru import logger

from schemas import Kline, TradeStatus

from settings import TIME_FORMAT, TRIGGER_PRICE_FALL_PER_MINUTE

from .actions import (
    get_klines_for_period,
    read_store_sell_price,
    read_store_sell_time,
    update_storage,
    write_state,
)


def check_change(list_klines: list[Kline], coin_name: str) -> bool:
    offset = -2
    coin_price = Decimal(list_klines[-1].close_price)
    sell_price = read_store_sell_price(coin_name)
    time_now = list_klines[-1].time_open
    sell_time_srt = read_store_sell_time(coin_name)
    sell_time = datetime.strptime(sell_time_srt, TIME_FORMAT)
    difference = time_now - sell_time
    difference_in_hours = timedelta(hours=1)
    if difference > difference_in_hours:
        logger.info("Ignore sell_price because passed more than 1 hour")
        sell_price = Decimal(1000000000)
    if sell_price == Decimal(0.0):
        sell_price = Decimal(1000000000)
        logger.info("Ignore sell_price. It must work only with the first start")

    change = 1 - list_klines[offset].open_price / list_klines[offset].close_price
    change_persent = Decimal(change).quantize(Decimal(".00001"), rounding=ROUND_DOWN)
    if change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE and coin_price < (sell_price * Decimal(0.99)):
        # logger.info(f"yes {item.time_open}")
        change_before = 1 - list_klines[offset - 1].open_price / list_klines[offset - 1].close_price
        if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE):
            logger.debug(f"Trigger to buy {coin_name} {change_persent=} time={list_klines[offset].time_open}")
            return True
    return False


def check_next_kline(list_klines: list[Kline]) -> bool:
    logger.info("Check_next_kline")
    offset = -2
    item = list_klines[offset]
    change = 1 - item.open_price / item.close_price
    # условие при котором проверяется сумарный рост предыдущих свечей
    # предыдущими свечками к примеру по 0.0001 рост может достич желаемого 0.001
    if change >= 0.001:
        logger.info(f"{list_klines[offset].close_price=}")
        return True
    return False


def buy(list_klines: list[Kline], coin_name: str, user_settings: dict):
    logger.error("Buy now -----")
    time_open = list_klines[-1].time_open.strftime(TIME_FORMAT)
    logger.error(f"time_open {time_open}")

    coin_price = list_klines[-1].close_price
    if coin_name == "BTC":
        amount = 0.00246
    else:
        amount = 6.0
    status_buy = False
    type_operation = TradeStatus.BUY

    action = update_storage(coin_name, coin_price, amount, status_buy, type_operation, time_open, user_settings)
    if action:
        logger.debug("Update_storage action in buy")
    else:
        logger.debug("Trouble with update_storage")
    write_state(coin_name, False)


def to_buy(user_settings: dict, coin_name: str, my_state: dict) -> tuple[str, bool]:
    list_klines = get_klines_for_period(coin_name, limit=60)

    message = ""
    send = True

    if my_state[coin_name]["checkTime"]:
        if check_next_kline(list_klines):
            text = f"Need to buy {coin_name}"
            logger.error(text)
            buy(list_klines, coin_name, user_settings)
        else:
            text = f"Need to check next kline {coin_name}"
            logger.info(text)
    else:
        if check_change(list_klines, coin_name):
            write_state(coin_name, True)
            text = f"Check_change {coin_name}"
            logger.info(text)
        else:
            text = f"No change to buy {coin_name}"
            logger.debug(text)
    message += text
    return message, send
