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


def get_max_price(list_of_price: list[Kline]) -> float:
    """Get maximum price

    :param list_of_price: list of prices
    :type list_of_price: list[Price]
    :return: maximum price
    :rtype: float
    """
    max_price = max([item.high_price for item in list_of_price])
    return max_price


class NoChangesError(Exception):
    """No Changes found"""


# def check_change(list_klines: list[Kline], coin_name: str, *, start: bool = False) -> datetime:
def check_change(list_klines: list[Kline], coin_name: str) -> bool:
    offset = -2
    # logger.info(f"{offset=}")
    coin_price = Decimal(list_klines[-1].close_price)
    sell_price = read_store_sell_price(coin_name)
    time_now = list_klines[-1].time_open
    sell_time_srt = read_store_sell_time(coin_name)
    sell_time = datetime.strptime(sell_time_srt, TIME_FORMAT)
    difference = time_now - sell_time
    difference_in_hours = timedelta(hours=1)
    if difference > difference_in_hours:
        logger.info("ignore sell_price because passed more than 1 hour")
        sell_price = Decimal(1000000000)
    if sell_price == Decimal(0.0):
        sell_price = Decimal(1000000000)
        logger.info("ignore sell_price. It must work only with the first start")

    # for item in list_klines[offset:]:
    #     change = 1 - item.open_price / item.close_price
    #     change_persent = Decimal(change).quantize(Decimal(".00001"), rounding=ROUND_DOWN)
    #     if change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE and coin_price < (sell_price * Decimal(0.99)):
    #         # logger.info(f"yes {item.time_open}")
    #         change_before = 1 - list_klines[offset - 1].open_price / list_klines[offset - 1].close_price
    #         if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE):
    #             # logger.info(f"{change_before=}")
    #             trigger_time = list_klines[-2].time_open
    #             check_time = trigger_time + timedelta(minutes=1)
    #             return check_time
    #     else:
    #         break
    # raise NoChangesError

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
    logger.info("check_next_kline")
    offset = -2
    item = list_klines[offset]
    change = 1 - item.open_price / item.close_price
    # if change > 0:
    if change >= 0.001:
        logger.info(f"{list_klines[offset].close_price=}")
        # logger.info("return True")
        return True
    # logger.info("return False")
    return False


def buy(list_klines: list[Kline], coin_name: str, user_settings: dict):
    logger.error("buy now -----")
    time_open = list_klines[-1].time_open.strftime(TIME_FORMAT)
    logger.error(f"list_klines[-1].time_open {time_open}")
    # bying order

    # get order info

    coin_price = list_klines[-1].close_price
    if coin_name == "BTC":
        amount = 0.00246
    else:
        amount = 6.0
    status_buy = False
    type_operation = TradeStatus.BUY

    action = update_storage(coin_name, coin_price, amount, status_buy, type_operation, time_open, user_settings)
    if action:
        logger.debug("update_storage action in buy")
    else:
        logger.debug("trouble with update_storage")
    write_state(coin_name, False)


def to_buy(user_settings: dict, coin_name: str, my_state: dict) -> tuple[str, bool]:
    list_klines = get_klines_for_period(coin_name, limit=60)

    message = ""
    send = True

    if my_state[coin_name]["checkTime"]:
        if check_next_kline(list_klines):
            text = f"need to buy {coin_name}"
            logger.error(text)
            buy(list_klines, coin_name, user_settings)
        else:
            # CHECK_TIME += timedelta(minutes=1)

            # time = datetime.fromtimestamp(float(my_state[coin_name]["checkTime"]) / 1e3) + timedelta(minutes=1)
            # timestamp = int(round(time.timestamp()))
            # write_state(coin_name, True)

            text = f"Need to check next kline {coin_name}"
            logger.info(text)
    else:
        # try:
        #     # CHECK_TIME = check_change_for_period(list_klines)
        #     # timestamp = int(round(check_change_for_period(list_klines).timestamp()))

        #     # CHECK_TIME = check_change(list_klines)
        #     timestamp = int(round(check_change(list_klines, coin_name).timestamp()))
        #     write_state(coin_name, True)
        #     # дописать функцию которая чекает предыдущие свечи на предмет падения

        #     text = f"check_change {coin_name}"
        #     logger.info(text)
        # except NoChangesError:
        #     text = f"NoChangesError {coin_name}"
        #     logger.debug(text)
        if check_change(list_klines, coin_name):
            write_state(coin_name, True)
            text = f"check_change {coin_name}"
            logger.info(text)
        else:
            text = f"No change to buy {coin_name}"
            logger.debug(text)
    message += text
    return message, send
