from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional

from loguru import logger

from connection import trade_market

from schemas import Kline, TradeStatus

from settings import (
    COEFFICIENT_WAIT_AFTER_SELL,
    COEFFICIENT_WAIT_FOR_BUY,
    ONLINE_TRADE,
    TIME_FORMAT,
    TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY,
)

from .actions import (
    get_klines_for_period,
    read_store_sell_price,
    read_store_sell_time,
    rounding_to_decimal,
    search_changes,
    update_storage,
    write_state,
)


def check_change(list_klines: List[Kline], coin_name: str) -> bool:
    """Checking for the trigger to buy

    :param list_klines: all Klines
    :type list_klines: List[Kline]
    :param coin_name: coin name (tiker)
    :type coin_name: str
    :return: result of these conditions
    :rtype: bool
    """
    offset = -2
    coin_price = Decimal(list_klines[-1].close_price)
    sell_price = read_store_sell_price(coin_name)
    time_now = list_klines[-1].time_open
    sell_time_srt = read_store_sell_time(coin_name)
    sell_time = datetime.strptime(sell_time_srt, TIME_FORMAT)
    difference = time_now - sell_time
    # difference_in_hours = timedelta(hours=1)
    difference_in_hours = timedelta(minutes=20)
    if difference > difference_in_hours:
        logger.info("Ignore sell_price because passed more than 1 hour")
        sell_price = Decimal(1000000000)
    if sell_price == Decimal(0.0):
        sell_price = Decimal(1000000000)
        logger.info("Ignore sell_price. It must work only with the first start")

    change_persent = get_rounded_change(list_klines[offset])
    first_condition = change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY
    second_condition = coin_price < (sell_price * COEFFICIENT_WAIT_AFTER_SELL)
    if first_condition and second_condition:
        change_before = get_rounded_change(list_klines[offset - 1])
        if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY):
            logger.debug(f"Trigger to buy {coin_name} {change_persent=} time={list_klines[offset].time_open}")
            return True
    return False


def check_old_kline(list_klines: List[Kline], offset: int, change: Decimal) -> bool:
    """Check old kline for growing up to COEFFICIENT_WAIT_FOR_BUY

    :param list_klines: all Klines
    :type list_klines: List[Kline]
    :param offset: start Klline to check
    :type offset: int
    :param change: change before
    :type change: Decimal
    :return: result of these conditions
    :rtype: bool
    """
    new_offset = offset - 1
    rounded_change = rounding_to_decimal(change)
    all_change = rounded_change
    for kline in list_klines[new_offset::-1]:
        rounded_new_change = get_rounded_change(kline)
        all_change += rounded_new_change
        if all_change >= COEFFICIENT_WAIT_FOR_BUY:
            logger.info("Old kline is grow up to trigger")
            logger.warning(f"All cange {all_change}")
            return True
        elif rounded_new_change < 0:
            logger.info("Fall not enough to buy")
            break
    return False


def check_next_kline(list_klines: List[Kline], fall: float) -> bool:
    """Check need to buy now or wait

    :param list_klines: all Klines
    :type list_klines: List[Kline]
    :param fall: past falling
    :type fall: float
    :return: result of these conditions
    :rtype: bool
    """
    logger.info("Check_next_kline")
    offset = -2
    item = list_klines[offset]
    change = get_rounded_change(item)
    rounded_fall = rounding_to_decimal(fall)
    if change >= COEFFICIENT_WAIT_FOR_BUY and change < abs(rounded_fall / 2):
        logger.info(f"{list_klines[offset].close_price=}")
        return True
    if check_old_kline(list_klines, offset, change):
        return True
    return False


def buy(list_klines: List[Kline], coin_name: str, user_settings: dict):
    """Execute buy. Write to history and send a command to the stock exchange

    :param list_klines: all Klines
    :type list_klines: List[Kline]
    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param user_settings: settings to write
    :type user_settings: dict
    """
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

    if ONLINE_TRADE:
        if coin_name == "BTC":
            trade_market(coin_name, type_operation, amount)

    write_state(coin_name, False, Decimal(0))


def get_rounded_change(item: Kline) -> Decimal:
    """Calculate changes and round it

    :param item: one Kline
    :type item: Kline
    :return: rounded change
    :rtype: Decimal
    """
    change = search_changes(item)
    return rounding_to_decimal(change)


def check_all_falling(list_klines: List[Kline]) -> Optional[Decimal]:
    """Calculating falling in percent with rounding

    :param list_klines: all Klines
    :type list_klines: List[Kline]
    :return: all falling in percent
    :rtype: Decimal
    """
    offset = -2
    new_offset = offset - 1
    rounded_change = get_rounded_change(list_klines[offset])
    if rounded_change < 0:
        all_change = rounded_change
        for kline in list_klines[new_offset::-1]:
            rounded_new_change = get_rounded_change(kline)
            if rounded_new_change >= 0:
                break
            all_change += rounded_new_change
        logger.warning(f"All falling {all_change}")
        return all_change
    return None


def to_buy(user_settings: dict, coin_name: str, my_state: dict) -> Tuple[str, bool]:
    """All decision logic

    :param user_settings: users settings
    :type user_settings: dict
    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param my_state: statement dictionary
    :type my_state: dict
    :return: string to send and state to send true
    :rtype: Tuple[str, bool]
    """
    list_klines = get_klines_for_period(coin_name, limit=60)

    message = ""
    send = True

    if my_state[coin_name]["checkTime"]:
        if check_next_kline(list_klines, my_state[coin_name]["fall"]):
            text = f"Need to buy {coin_name}"
            logger.error(text)
            buy(list_klines, coin_name, user_settings)
        else:
            change_persent = check_all_falling(list_klines)
            write_state(coin_name, True, change_persent)
            text = f"Need to check next kline {coin_name}"
            logger.info(text)
    else:
        if check_change(list_klines, coin_name):
            change_persent = check_all_falling(list_klines)
            write_state(coin_name, True, change_persent)
            text = f"Check_change {coin_name}"
            logger.info(text)
        else:
            text = f"No change to buy {coin_name}"
            logger.debug(text)
    message += text
    return message, send
