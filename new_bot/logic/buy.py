import json
from enum import Enum, unique
from datetime import datetime
from collections import namedtuple
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from threading import local
import attr

from loguru import logger

from connection import client
from settings import COEFFICIENT_FOR_PROFIT, TRIGGER_PRICE_FALL_PER_MINUTE
from pydantic import BaseModel


def str_to_datetime(item: str) -> datetime:
    return datetime.fromtimestamp(float(item) / 1e3)


@unique
class TradeStatus(str, Enum):
    START = "start"
    BUY = "buy"
    SELL = "sell"


class AmountCoin(float, Enum):
    BTC = 0.00246
    LUNA = 1.0
    NEAR = 6.0


@attr.s
class Kline:
    time_open: datetime = attr.ib(converter=str_to_datetime)
    open_price: float = attr.ib(converter=float)
    high_price: float = attr.ib(converter=float)
    low_price: float = attr.ib(converter=float)
    close_price: float = attr.ib(converter=float)
    volume: float = attr.ib(converter=float)  # объем прошедший за минуту
    time_close: datetime = attr.ib(converter=str_to_datetime)
    quote_asset_volume: float = attr.ib(converter=float)
    count_trades: int = attr.ib()
    base_volume: float = attr.ib(
        converter=float
    )  # объем который вкинули по рыночной цене(киты) Taker buy base asset volume
    quote_volume: float = attr.ib(converter=float)  # Taker buy quote asset volume
    # ignore_time: datetime = attr.ib(converter=str_to_datetime)
    ignore_time: int = attr.ib(converter=int)


def should_i_buy(price_fall: float, desired_fall: float, current_price: float) -> bool:
    """Calculate need to buy now or not

    :param price_fall: difference between the maximum and current price
    :type price_fall: float
    :param desired_fall: percent we need to drop
    :type desired_fall: float
    :param current_price: coin's current price in stable USDT. 1USDT ~ 1$ USA
    :type current_price: float
    :return: True if you should buy, False otherwise
    :rtype: bool
    """
    # Example: 21 / 200 * 100 == 10.5% and 10.5 >= 10, so -> True
    # if price_fall / current_price * 100 >= desired_fall:
    profit = float(COEFFICIENT_FOR_PROFIT) + (float(desired_fall) / 100) - 1
    # Example: 300 / 40516 == 0.0074 and 0.0074 >=  0,00665, so -> True  desired_fall = 0.5
    if price_fall / current_price >= profit:  # 0,00665
        return True
    return False


def is_time_to_buy(coin: dict, coin_price: float, price_fall: float) -> bool:

    if should_i_buy(price_fall, coin["desiredPriceFall"], coin_price):
        return True

    return False


def get_klines_for_period(coin_name: str, *, interval: str = "1m", limit: int = 240) -> list[Kline]:
    """Get maximum price

    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc., defaults to "1m"
    :type interval: str, optional
    :param limit: the limit of kline. Default 240, min 1, max 1000,
    :type limit: str, optional
    :return: klines list
    :rtype: float
    """
    trading_pair = f"{coin_name}USDT"
    prices = client.klines(trading_pair, interval, limit=limit)
    klines_list = [Kline(*item) for item in prices]
    return klines_list


def get_max_price(list_of_price: list[Kline]) -> float:
    """Get maximum price

    :param list_of_price: list of prices
    :type list_of_price: list[Price]
    :return: maximum price
    :rtype: float
    """
    max_price = max([item.high_price for item in list_of_price])
    return max_price


# def get_max_price(coin_name: str, *, interval: str = "1m") -> float:
#     """Get maximum price

#     :param coin_name: coin name (tiker)
#     :type coin_name: str
#     :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc., defaults to "1m"
#     :type interval: str, optional
#     :return: maximum price
#     :rtype: float
#     """
#     trading_pair = f"{coin_name}USDT"
#     max_price = float(client.klines(trading_pair, interval, limit=240)[-1][2])
#     return max_price


def get_stat(current_price: float, coin_name: str, *, interval: str = "1h") -> float:
    """Get the difference between the maximum and current price

    :param current_price: current price
    :type current_price: float
    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc., defaults to "1h"
    :type interval: str, optional
    :return: Change between the maximum and current price
    :rtype: float
    """
    max_price = get_max_price(coin_name, interval=interval)
    return max_price - current_price


def update_storage(
    coin_name: str, coin_price: float, amount: float, status_buy: bool, type_operation: str, user_settings: dict = None
) -> bool:
    """
    Function to update storage

    :param coin_name: coin name
    :type coin_name: str
    :param coin_price: coin price
    :type coin_price: float
    :param amount: amount of coin
    :type amount: float
    :param status_buy: trade status
    :type status_buy: bool
    :param type_operation: operation type
    :type type_operation: str
    :param user_settings: dict with user setting, defaults to None
    :type user_settings: dict, optional
    :return: status of update True or False
    :rtype: bool
    """
    try:
        with open("storage.json", "r+", encoding="utf8") as my_coins_data:
            my_coins = json.loads(my_coins_data.read())
            # if type_operation == TradeStatus.BUY.value:
            if type_operation == TradeStatus.BUY:
                my_coins[coin_name]["buyPrice"] = coin_price
                stop_loss_price = coin_price * user_settings["stop_loss_ratio"]
                my_coins[coin_name]["stopLossPrice"] = stop_loss_price
                # logger.info(f"Write buyPrice = {coin_price}")
                # logger.info(f"Write stop_loss_price = {stop_loss_price}")
                # logger.info(f"Write stop_loss_ratio = {user_settings['stop_loss_ratio']}")
            else:
                possible_profit = count_profit(my_coins[coin_name], coin_price)
                my_coins[coin_name]["buyPrice"] = 0.0
                my_coins[coin_name]["stopLossPrice"] = 0.0
                my_coins[coin_name]["balanse"] += possible_profit
            # my_coins[coin_name]['currentPrice'] = coin_price
            my_coins[coin_name]["history"][type_operation].append(coin_price)
            my_coins[coin_name]["amount"] = amount
            my_coins[coin_name]["status"]["buy"] = status_buy
            # if user_settings:
            #     my_coins[coin_name]['stopLossPrice'] = coin_price * user_settings['stop_loss_ratio']

            try:
                CoinInfo.parse_obj(my_coins[coin_name])
            except ValidationError as e:
                raise TypeError(f"'{coin_name}' does not match the schema CoinInfo {e.json()}")
            my_coins_data.seek(0)
            my_coins_data.write(json.dumps(my_coins, sort_keys=True, indent=2))
            my_coins_data.truncate()
        return True

    except Exception as err:
        logger.error(f"{err=}")
        return False


# def check_change(list_klines: list[Kline], *, start: bool = False) -> bool:
#     # start_num = -2
#     # if start:
#     #     start_num = 0
#     # logger.info(f"{start_num=}")
#     # for number, item in enumerate(list_klines[:start_num:-1], 1000):

#     start_num = -1
#     if start:
#         start_num = 0
#     logger.info(f"{start_num=}")
#     last_down = 0.0
#     for number, item in enumerate(list_klines[start_num:], 1):
#         # change = 1 - list_klines[-2].open_price / list_klines[-2].close_price
#         # logger.info(f"{change=} {type(change)}")
#         # logger.info(f"open_price={list_klines[-2].open_price} close_price={list_klines[-2].close_price}")
#         # logger.info(f"time_open={list_klines[-2].time_open}")
#         # logger.info(f"time_close={list_klines[-2].time_close}")
#         change = 1 - item.open_price / item.close_price
#         # logger.info(f"{change=} {type(change)}")
#         # logger.info(f"open_price={item.open_price} close_price={item.close_price}")
#         # logger.info(f"time_open={item.time_open}")
#         # logger.info(f"time_close={item.time_close}")
#         change_persent = Decimal(change).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
#         # logger.info(f"{change_persent=} {number=} ")
#         if change_persent <= TRIGGER_PRICE_FALL_PER_MINUTE:
#             logger.info(f"yes {number=} {item.time_open}")
#             # global last_down
#             last_down = change
#             if number >= 1:
#                 # list_klines[number - 1]
#                 change_before = 1 - list_klines[number - 1].open_price / list_klines[number - 1].close_price
#                 if change_before < abs(change_persent + 0.0020):
#                     return True
#         # else:
#         #     logger.info("no")
#     logger.info(f"{last_down=}")
#     return True


# def check_change(list_klines: list[Kline], *, start: bool = False) -> bool:
#     start_num = -1
#     logger.info(f"{start_num=}")
#     last_down = 0.0
#     for item in list_klines[start_num:]:
#         change = 1 - item.open_price / item.close_price
#         change_persent = Decimal(change).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
#         if change_persent <= TRIGGER_PRICE_FALL_PER_MINUTE:
#             logger.info(f"yes {item.time_open}")
#             # global last_down
#             last_down = change
#             change_before = 1 - list_klines[start_num - 1].open_price / list_klines[start_num - 1].close_price
#             if change_before < abs(change_persent + 0.0020):
#                 logger.info(f"{change_before=}")
#                 return True
#     logger.info(f"{last_down=}")
#     return True


def check_change(list_klines: list[Kline], *, start: bool = False) -> bool:
    start_num = -1
    logger.info(f"{start_num=}")
    last_down = 0.0
    for item in list_klines[start_num:]:
        change = 1 - item.open_price / item.close_price
        change_persent = Decimal(change).quantize(Decimal(".00001"), rounding=ROUND_DOWN)
        if change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE:
            # if change_persent <= -0.001:
            logger.info(f"yes {item.time_open}")

            last_down = change
            change_before = 1 - list_klines[start_num - 1].open_price / list_klines[start_num - 1].close_price
            if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE):
                logger.info(f"{change_before=}")
                return True
    logger.info(f"{last_down=}")
    return False


def check_change(list_klines: list[Kline], *, start: bool = False) -> bool:
    start_num = -1
    logger.info(f"{start_num=}")
    last_down = 0.0
    for item in list_klines[start_num:]:
        change = 1 - item.open_price / item.close_price
        change_persent = Decimal(change).quantize(Decimal(".00001"), rounding=ROUND_DOWN)
        if change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE:
            # if change_persent <= -0.001:
            logger.info(f"yes {item.time_open}")

            last_down = change
            change_before = 1 - list_klines[start_num - 1].open_price / list_klines[start_num - 1].close_price
            if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE):
                logger.info(f"{change_before=}")
                return True
    logger.info(f"{last_down=}")
    return False


def check_change_for_period(list_klines: list[Kline], *, start: bool = False) -> bool:
    last_down = 0.0
    for number, item in enumerate(list_klines):
        change = 1 - item.open_price / item.close_price
        change_persent = Decimal(change).quantize(Decimal(".00001"), rounding=ROUND_DOWN)
        # logger.info(f"yes {number=}")
        if change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE:
            # if change_persent <= -0.001:
            logger.info(f"yes {item.time_open}")
            # last_down = change
            if number > 0:
                change_before = 1 - list_klines[number - 1].open_price / list_klines[number - 1].close_price
                if change_before < 0.001 and change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE):
                    # if change_before < abs(change_persent + Decimal(0.0020)):
                    last_down = change
                    logger.info(f"{change_before=}")
                    logger.info(f"{change_persent + TRIGGER_PRICE_FALL_PER_MINUTE}")
                    # return True
    logger.info(f"{last_down=}")
    return True


# def to_buy(coin: dict, coin_price: float, coin_name: str, send: bool, update: bool, user_settings: dict) -> tuple:
#     """Buy logic

#     :param coin: all info
#     :type coin: dict
#     :param coin_price: coin price
#     :type coin_price: float
#     :param coin_name: coin name (tiker)
#     :type coin_name: str
#     :param send: senr or not to TG
#     :type send: bool
#     :param update: need to update in DB or not
#     :type update: bool
#     :param user_settings: dictionary of options
#     :type user_settings: dict
#     :return: need to send or not bool and list messages
#     :rtype: tuple
#     """
#     message = ""


def to_buy():
    list_klines = get_klines_for_period("BTC", limit=1000)

    # check_change(list_klines, start=True)
    # check_change(list_klines)

    check_change_for_period(list_klines)

    # price_fall = get_stat(coin_price, coin_name)
    # if not is_time_to_buy(coin, coin_price, price_fall):
    #     message += f"{coin_name} --> nothing to do right now... price {coin_price}"
    #     return (message, send, update)
    # message = ""
    # message += f"{coin_name} --> TIME TO BUY price {coin_price}\n"
    # message += f"price fall = {round(price_fall / coin_price * 100, 3)}%"
    # send = True
    # update = True
    # amount = AmountCoin[coin_name]
    # status_buy = False
    # logger.info(f"{coin_name=} {coin_price=} {amount=} {status_buy=}")
    # logger.info(f"{user_settings=}")

    # # # Not needed now
    # # price_stop_loss = get_stop_loss_price(coin_price, user_settings["stop_loss_ratio"])
    # # set_order_with_stop_loss(coin_name, price_stop_loss, coin["stopLossPrice"], amount)

    # if not update_storage(coin_name, coin_price, amount, status_buy, "buy", user_settings):
    #     logger.info("Something wrong with update storage")

    # return (message, send, update)


class Deal:
    pass


class Buy:
    pass


class BuyWithStopLoss(Buy):
    pass
