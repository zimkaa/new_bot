from decimal import Decimal, ROUND_DOWN

from loguru import logger

from schemas import Kline, TradeStatus

from settings import COEFFICIENT_FOR_PROFIT, TIME_FORMAT, TRIGGER_PRICE_FALL_PER_MINUTE

from .actions import (
    get_klines_for_period,
    read_store_buy_price,
    # read_store_stop_loss_price,
    reed_store,
    update_stop_loss_price,
    update_storage,
)


def rounding(some_value: float) -> Decimal:
    return Decimal(some_value).quantize(Decimal(".00001"), rounding=ROUND_DOWN)


def search_changes(item: Kline) -> Decimal:
    change = 1 - item.open_price / item.close_price
    return Decimal(change)


def check_change_proffit(coin_name: str, item: Kline, list_klines: list[Kline], coin_info: float) -> bool:
    price = read_store_buy_price(coin_name)
    profit_price = price * COEFFICIENT_FOR_PROFIT
    # stop_loss_price = read_store_stop_loss_price(coin_name)
    stop_loss_price = coin_info["stopLossPrice"]

    if stop_loss_price > Decimal(list_klines[-2].close_price):
        logger.warning(f"Stoploss sell {coin_name}")
        logger.error(f"We need to sell now {coin_name} {list_klines[-1].time_open}")
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


def should_i_sell(rounded_change: Decimal, offset: int, list_klines: list[Kline], coin_info: float) -> bool:
    change_before = rounded_change
    stop_loss_price = coin_info["stopLossPrice"]
    buy_price = coin_info["buyPrice"]
    new_offset = offset - 1
    for element in list_klines[new_offset::-1]:
        change = search_changes(element)
        rounded_change = rounding(change)
        if change_before <= -TRIGGER_PRICE_FALL_PER_MINUTE and stop_loss_price > list_klines[-2].close_price:
            logger.error(f"Sell info We need to sell time_open={list_klines[-1].time_open}")
            logger.error(f"Sell info Now_close_price={list_klines[-1].close_price}")
            logger.error(f"Sell info All changes {change_before} stop_loss_price={stop_loss_price}")
            return True
        elif (buy_price * 1.005) < list_klines[offset].close_price and stop_loss_price < list_klines[-1].close_price:
            logger.error(f"Sell info Stop_loss_price={stop_loss_price} close_ptice={list_klines[offset].close_price}")
            logger.error(
                f"Sell info Now_close_price={list_klines[-1].close_price} time_open={list_klines[-1].time_open}"
            )
            return True
        elif rounded_change > 0:
            logger.info("Fall not enough to sell")
            break
        else:
            # logger.info(f"Add to change_before {element.close_price=}")
            change_before += rounded_change
    logger.warning("I wait a string before <Fall not enough to sell>")
    return False


def check_fall(list_klines: list[Kline], coin_name: str) -> bool:
    kline_offset = -2
    item = list_klines[kline_offset]
    change = search_changes(item)
    logger.info(f"Start check_fall close_price={item.close_price} time_open={item.time_open}")
    rounded_change = rounding(change)
    if rounded_change < 0:
        coin_info = reed_store(coin_name)
        if rounded_change <= -TRIGGER_PRICE_FALL_PER_MINUTE:
            return check_change_proffit(coin_name, item, list_klines, coin_info)
        else:
            logger.info(f"Check should_i_sell {coin_name}")
            return should_i_sell(rounded_change, kline_offset, list_klines, coin_info)

    logger.info(f"We have a grow {coin_name}")
    buy_price = reed_store(coin_name)["buyPrice"]
    if item.low_price > (buy_price * 1.005):
        new_stop_loss = item.low_price * 0.998
        update_stop_loss_price(coin_name, new_stop_loss)
        logger.debug(f"WE UPDATE STOP LOSS PRICE {coin_name} to {new_stop_loss}")
    return False


def to_sell(user_settings: dict, coin_name: str, my_state: dict) -> tuple[str, bool]:
    list_klines = get_klines_for_period(coin_name, limit=200)

    message = ""
    send = True

    if check_fall(list_klines, coin_name):
        coin_price = list_klines[-1].close_price
        if coin_name == "BTC":
            amount = 0.00246
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
        text = f"Need to sell {coin_name} time_open {time_sell}"
        logger.error(text)
        message += text
    else:
        last_kline_time = list_klines[-1].time_open.strftime(TIME_FORMAT)
        text = f"Not time to sell yet {coin_name} {last_kline_time}"
        logger.debug(text)
        message += text

    return message, send
