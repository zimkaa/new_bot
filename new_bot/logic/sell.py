from decimal import Decimal
from typing import List, Tuple

from loguru import logger

from connection import trade_market

from schemas import Kline, TradeStatus

from settings import (
    COEFFICIENT_DOWN_TO,
    COEFFICIENT_FOR_PROFIT,
    COEFFICIENT_RISE_UP_TO,
    TIME_FORMAT,
    TRIGGER_PRICE_FALL_PER_MINUTE,
    ONLINE_TRADE,
)

from .actions import (
    get_klines_for_period,
    read_store_buy_price,
    reed_store,
    rounding_to_decimal,
    rounding_to_float,
    search_changes,
    update_stop_loss_price,
    update_storage,
)


def check_change_proffit(coin_name: str, item: Kline, list_klines: List[Kline], coin_info: dict) -> bool:
    price = read_store_buy_price(coin_name)
    profit_price = price * COEFFICIENT_FOR_PROFIT
    stop_loss_price = Decimal(coin_info["stopLossPrice"])

    if stop_loss_price > Decimal(list_klines[-2].close_price):
        logger.warning(f"Stoploss sell check_change_proffit {coin_name}")
        logger.debug(f"Down is more then TRIGGER_PRICE_FALL_PER_MINUTE {-TRIGGER_PRICE_FALL_PER_MINUTE}")
        logger.error(f"We need to sell now check_change_proffit {coin_name} {list_klines[-1].time_open}")
        return True

    if profit_price < stop_loss_price:
        profit_price = stop_loss_price
        logger.debug(f"Profit_price < stop_loss_price --- swapped {list_klines[-1].time_open} {coin_name}")

    if Decimal(item.close_price) > profit_price:
        logger.error(f"We need to sell now {coin_name} {list_klines[-1].time_open}")
        logger.error(f"Close_price > profit_price {Decimal(item.close_price)} > {profit_price} {coin_name}")
        return True

    logger.warning(f"Fall not enough to sell {coin_name} {list_klines[-1].time_open}")
    logger.warning(f"Stop loss price={stop_loss_price} price={list_klines[-2].close_price}")
    return False


def should_i_sell(rounded_change: Decimal, offset: int, list_klines: List[Kline], coin_info: dict) -> bool:
    change_before = rounded_change
    stop_loss_price = coin_info["stopLossPrice"]
    buy_price = Decimal(coin_info["buyPrice"])
    new_offset = offset - 1
    # reversed_list_klines = list_klines[::-1]  # Not right!!!
    # for element in reversed_list_klines[new_offset:]:  # Not right!!!
    for element in list_klines[new_offset::-1]:
        change = search_changes(element)
        rounded_change = rounding_to_decimal(change)
        # # This is trap to me. It never check because stop_loss_price always < list_klines[-2].close_price
        # if change_before <= -TRIGGER_PRICE_FALL_PER_MINUTE and stop_loss_price > list_klines[-2].close_price:
        if change_before <= -TRIGGER_PRICE_FALL_PER_MINUTE:
            logger.error(f"Sell info We need to sell time_open={list_klines[-1].time_open}")
            logger.error(f"Sell info Now_close_price={list_klines[-1].close_price}")
            logger.error(f"Sell info All changes {change_before} stop_loss_price={stop_loss_price}")
            return True
        # # This is trap to me
        # elif (buy_price * COEFFICIENT_RISE_UP_TO) < list_klines[offset].close_price and stop_loss_price < list_klines[
        #     -1
        # ].close_price:
        #     # # This is trap to me
        #     logger.error(f"Sell info Stop_loss_price={stop_loss_price} close_ptice={list_klines[offset].close_price}")
        #     logger.error(
        #         f"Sell info Now_close_price={list_klines[-1].close_price} time_open={list_klines[-1].time_open}"
        #     )
        #     logger.warning("Sell with profit!!!")
        #     return True
        elif rounded_change > 0:
            logger.info("Fall not enough to sell")
            break
        else:
            # logger.info(f"Add to change_before {element.close_price=}")
            change_before += rounded_change
    logger.warning("I wait a string before <Fall not enough to sell>")
    return False


def check_stop_loss(list_klines: List[Kline], coin_name: str) -> bool:
    kline_offset = -2
    close_price = Decimal(list_klines[kline_offset].close_price)

    coin_info = reed_store(coin_name)
    stop_loss_price = coin_info["stopLossPrice"]

    if stop_loss_price > close_price:
        logger.warning(f"Stoploss sell {coin_name} price now {list_klines[-1].close_price}")
        logger.error(f"We need to sell now {coin_name} {list_klines[-1].time_open}")
        return True
    return False


def check_fall(list_klines: List[Kline], coin_name: str) -> bool:
    kline_offset = -2
    item = list_klines[kline_offset]
    logger.info(f"Start check_fall close_price={item.close_price} time_open={item.time_open}")
    # # SELL ONLY WHEN STOP LOSS PRISE
    # change = search_changes(item)
    # rounded_change = rounding_to_decimal(change)
    # if rounded_change < 0:
    #     coin_info = reed_store(coin_name)
    #     if rounded_change <= -TRIGGER_PRICE_FALL_PER_MINUTE:
    #         logger.info(f"Check check_change_proffit {coin_name}")
    #         return check_change_proffit(coin_name, item, list_klines, coin_info)
    #     else:
    #         logger.info(f"Check should_i_sell {coin_name}")
    #         return should_i_sell(rounded_change, kline_offset, list_klines, coin_info)

    change = search_changes(item)
    rounded_change = rounding_to_decimal(change)
    if rounded_change > 0:
        logger.info(f"We have a grow {coin_name} up to {rounded_change}")
    else:
        logger.info(f"We have a fall {coin_name} down to {rounded_change}")
    buy_price = Decimal(reed_store(coin_name)["buyPrice"])
    coin_info = reed_store(coin_name)
    stop_loss_price = Decimal(coin_info["stopLossPrice"])
    new_stop_loss = Decimal(item.low_price) * COEFFICIENT_DOWN_TO
    if item.low_price > (buy_price * COEFFICIENT_RISE_UP_TO) and new_stop_loss > stop_loss_price:
        action = update_stop_loss_price(coin_name, rounding_to_float(new_stop_loss))
        if action:
            logger.debug("update_stop_loss_price action in check_fall")
        else:
            logger.warning("Trouble with update_stop_loss_price")
        logger.debug(f"WE UPDATE STOP LOSS PRICE {coin_name} to {new_stop_loss}")
        logger.warning(f"NOW PRICE to {list_klines[-1].close_price}")
    return False


def to_sell(user_settings: dict, coin_name: str, my_state: dict) -> Tuple[str, bool]:
    list_klines = get_klines_for_period(coin_name, limit=60)

    message = ""
    send = True

    if check_stop_loss(list_klines, coin_name):
        stop_loss_reason = True
        coin_price = list_klines[-1].close_price
        if coin_name == "BTC":
            amount = 0.00245
        else:
            amount = 6.0
        status_buy = True
        type_operation = TradeStatus.SELL
        time_sell = list_klines[-1].time_open.strftime(TIME_FORMAT)
        action = update_storage(
            coin_name, coin_price, amount, status_buy, type_operation, time_sell, user_settings, stop_loss_reason
        )
        if action:
            logger.debug("Update_storage action in check_fall")
        else:
            logger.warning("Trouble with update_storage")

        if ONLINE_TRADE:
            if coin_name == "BTC":
                trade_market(coin_name, type_operation, amount)

        text = f"Need to sell {coin_name} time_open {time_sell}"
        logger.error(text)
        message += text
    else:
        if check_fall(list_klines, coin_name):
            coin_price = list_klines[-1].close_price
            if coin_name == "BTC":
                amount = 0.00245
            else:
                amount = 6.0
            status_buy = True
            type_operation = TradeStatus.SELL
            time_sell = list_klines[-1].time_open.strftime(TIME_FORMAT)
            action = update_storage(coin_name, coin_price, amount, status_buy, type_operation, time_sell, user_settings)
            if action:
                logger.debug("Update_storage action in check_fall")
            else:
                logger.warning("Trouble with update_storage")

            if ONLINE_TRADE:
                if coin_name == "BTC":
                    trade_market(coin_name, type_operation, amount)

            text = f"Need to sell {coin_name} time_open {time_sell}"
            logger.error(text)
            message += text
        else:
            last_kline_time = list_klines[-1].time_open.strftime(TIME_FORMAT)
            text = f"Not time to sell yet {coin_name} {last_kline_time}"
            logger.debug(text)
            message += text

    return message, send
