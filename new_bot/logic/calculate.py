import json
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from enum import Enum, unique
from typing import Optional, Dict

from loguru import logger
from pydantic import BaseModel, ValidationError

# from trade import logger
from connection import client
from settings import COEFFICIENT_FOR_PROFIT
from local_schema import Settings, Ratios, CoinInfo


class AmountCoin(float, Enum):
    BTC = 0.00246
    LUNA = 1.0
    NEAR = 6.0


@unique
class TradeStatus(str, Enum):
    START = "start"
    BUY = "buy"
    SELL = "sell"


def get_price(coin_name: str) -> float:
    """Gets the price of the coin

    :param coin_name: coin name (tiker)
    :type coin_name: str
    :return: coin price
    :rtype: float
    """
    trading_pair = f"{coin_name}USDT"
    # return float(client.avg_price(trading_pair)["price"])
    price = client.ticker_price(trading_pair)["price"]
    # logger.error(f"{price=} type {type(price)}")
    # logger.error(f"{float(price)} type {type(float(price))}")
    return float(price)


def choose_an_action(status: bool = None) -> str:
    """
    Choose the next action

    :param status: status, defaults to None
    :type status: bool, optional
    :return: name of the doing
    :rtype: str
    """
    if status is None:
        # first start
        return TradeStatus.START
    if status:
        # start buy
        return TradeStatus.BUY
    # start sell
    return TradeStatus.SELL


def get_max_price(coin_name: str, *, interval: str = "1m") -> float:
    """Get maximum price

    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc., defaults to "1m"
    :type interval: str, optional
    :return: maximum price
    :rtype: float
    """
    trading_pair = f"{coin_name}USDT"
    # max_price = float(client.klines(trading_pair, interval, limit=1)[-1][2])
    max_price = client.klines(trading_pair, interval, limit=4)
    return max_price


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


def get_min_price(coin_name: str, *, interval: str = "1m") -> float:
    """Get minimum price

    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc., defaults to "1m"
    :type interval: str, optional
    :return: minimum price
    :rtype: float
    """
    trading_pair = f"{coin_name}USDT"
    min_price = float(client.klines(trading_pair, interval, limit=1)[-1][3])
    return min_price


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


def get_stop_loss_price(price: float, stop_loss_ratio: float) -> float:
    """Create stop loss order

    :param price: current price
    :type price: float
    :param stop_loss_ratio: selling coefficient
    :type stop_loss_ratio: float
    :return: stop loss price
    :rtype: float
    """
    price_stop_loss = price * stop_loss_ratio
    logger.info(f"Create stop loss price {price_stop_loss}")
    return price_stop_loss


def set_order_with_stop_loss(
    coin_name: str,
    price_stop_loss: float,
    old_price_stop_loss: float,
    *,
    amount: float = None,
):
    """Need to write new code

    :param coin_name: coin name. Examle: 'BTC'
    :type coin_name: str
    :param price_stop_loss: price for immediately sell Examle: 35000
    :type price_stop_loss: float
    :param old_price_stop_loss: old price for immediately sell Examle: 34000
    :type old_price_stop_loss: float
    :param amount: amount of coin to sell, defaults to None
    :type amount: float, optional
    """
    try:
        logger.info(f"All Good! {coin_name=} stop_loss={price_stop_loss} {amount=}")
        with open("test.json", "r+", encoding="utf8") as my_coins_data:
            my_coins = json.loads(my_coins_data.read())
            if not amount and my_coins[coin_name]["operations"]:
                amount = my_coins[coin_name]["operations"][-1]["amount"]
            operations_dict = {
                "amount": amount,
                "oldStopLoss": old_price_stop_loss,
                "price_stop_loss": price_stop_loss,
            }
            my_coins[coin_name]["operations"].append(operations_dict)

            my_coins_data.seek(0)
            my_coins_data.write(json.dumps(my_coins, sort_keys=True, indent=2))
            my_coins_data.truncate()
    except Exception as err:
        logger.error(f"Something rong with query stop loss \n {err}")


def count_profit(coin: dict, current_price: float) -> float:
    """Get rounded profit

    coin - e.g.:
                {"amount": 1.4466,
                "buyPrice": 200,
                "desiredPriceFall":  10}

    :param coin: dict of info about coin
    :type coin: dict
    :param current_price: coin's current price in stable USDT. 1USDT ~ 1$ USA
    :type current_price: float
    :return: rounded profit in USDT
    :rtype: float
    """
    # Example: (220 - 200) * 0.5 == 10
    # get_profit(coin['buyPrice'])
    no_proffit_sell = coin["buyPrice"] * float(COEFFICIENT_FOR_PROFIT)
    return round((current_price - no_proffit_sell) * coin["amount"], 3)


def update_storage(
    coin_name: str,
    coin_price: float,
    amount: float,
    status_buy: bool,
    type_operation: str,
    user_settings: dict = None,
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
                stopLossPrice = coin_price * user_settings["stop_loss_ratio"]
                my_coins[coin_name]["stopLossPrice"] = stopLossPrice
                # logger.info(f"Write buyPrice = {coin_price}")
                # logger.info(f"Write stopLossPrice = {stopLossPrice}")
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


def to_buy(coin: dict, coin_price: float, coin_name: str, send: bool, update: bool, user_settings: dict) -> tuple:
    """Buy logic

    :param coin: all info
    :type coin: dict
    :param coin_price: coin price
    :type coin_price: float
    :param coin_name: coin name (tiker)
    :type coin_name: str
    :param send: senr or not to TG
    :type send: bool
    :param update: need to update in DB or not
    :type update: bool
    :param user_settings: dictionary of options
    :type user_settings: dict
    :return: need to send or not bool and list messages
    :rtype: tuple
    """
    message = ""
    price_fall = get_stat(coin_price, coin_name)
    # max_price = price_fall + coin_price
    # logger.info(f'Max price per 1H {max_price=}')
    # profit = (float(COEFFICIENT_FOR_PROFIT) + (float(coin['desiredPriceFall']) / 100) - 1)
    # logger.info(f"Price buy {(1 - profit) * max_price}")
    if not is_time_to_buy(coin, coin_price, price_fall):
        message += f"{coin_name} --> nothing to do right now... price {coin_price}"
        return (message, send, update)
    message = ""
    message += f"{coin_name} --> TIME TO BUY price {coin_price}\n"
    message += f"price fall = {round(price_fall / coin_price * 100, 3)}%"
    send = True
    update = True
    amount = AmountCoin[coin_name]
    status_buy = False
    logger.info(f"{coin_name=} {coin_price=} {amount=} {status_buy=}")
    logger.info(f"{user_settings=}")

    # # Not needed now
    # price_stop_loss = get_stop_loss_price(coin_price, user_settings["stop_loss_ratio"])
    # set_order_with_stop_loss(coin_name, price_stop_loss, coin["stopLossPrice"], amount)

    if not update_storage(coin_name, coin_price, amount, status_buy, "buy", user_settings):
        logger.info("Something wrong with update storage")

    return (message, send, update)


def is_time_to_sell(coin: dict, coin_price: float) -> bool:
    stop_loss_sell = coin_price < coin["stopLossPrice"]
    if stop_loss_sell:
        return True
    return False


def update_stop_loss_price(coin_name: str, stop_loss_price: float):
    try:
        with open("storage.json", "r+", encoding="utf8") as my_coins_data:
            my_coins = json.loads(my_coins_data.read())
            my_coins[coin_name]["stopLossPrice"] = stop_loss_price
            try:
                CoinInfo.parse_obj(my_coins[coin_name])
            except ValidationError as e:
                raise TypeError(f"'{coin_name}' does not match the schema CoinInfo {e.json()}")
            my_coins_data.seek(0)
            my_coins_data.write(json.dumps(my_coins, sort_keys=True, indent=2))
            my_coins_data.truncate()
            # logger.info(f'Set new {stop_loss_price=}')
        return True

    except Exception:
        return False


def to_sell(
    coin: dict,
    coin_price: float,
    coin_name: str,
    send: bool,
    update: bool,
    user_settings: dict = None,
) -> Optional[tuple]:
    message = ""
    # send = False
    if not is_time_to_sell(coin, coin_price):
        min_price = get_min_price(coin_name, interval="1m")
        min_profit_sell = coin["buyPrice"] * float(COEFFICIENT_FOR_PROFIT)
        min_price_to_cange = min_profit_sell * user_settings["min_price_ratio"]

        if coin["stopLossPrice"] <= min_price_to_cange:
            new_stop_loss = user_settings["stop_loss_ratio"]
            if min_price >= min_price_to_cange:
                new_stop_loss = min_price * user_settings["stop_loss_ratio"]
                if new_stop_loss > coin["stopLossPrice"] * 1.0006:
                    # # Not needed yet
                    # set_order_with_stop_loss(
                    #     coin_name, new_stop_loss, coin["stopLossPrice"]
                    # )
                    # update_stop_loss_price(coin_name, new_stop_loss)

                    # # Old
                    # update_stop_loss_price(coin_name, min_price)
                    logger.debug("stopLossPrice <= min_price_to_cange and min_pricemin_price >= min_price_to_cange")
                    logger.debug(f"{new_stop_loss=}")
                    message += f"{coin_name} --> Set new stop loss {new_stop_loss=}$\n"
                    send = True
                    update = True
        else:
            new_stop_loss = min_price * user_settings["stop_loss_ratio"]
            if coin["stopLossPrice"] < new_stop_loss:
                logger.debug("stopLossPrice > min_price_to_cange and stopLossPrice < new_stop_loss")
                logger.debug(f"{new_stop_loss=}")
                # # Not needed yet
                # set_order_with_stop_loss(
                #     coin_name, new_stop_loss, coin["stopLossPrice"]
                # )

                message += f"{coin_name} --> Set new stop loss {new_stop_loss=}$\n"
                send = True
                update = True
        update_stop_loss_price(coin_name, new_stop_loss)

        # if min_price > coin['stopLossPrice'] and min_price > min_profit_sell:
        #     new_stop_loss = min_price * user_settings['stop_loss_ratio']
        #     update_stop_loss_price(coin_name, new_stop_loss)
        #     message += f'{coin_name} --> Set new stop loss {min_price=}$\n'
        #     send = True

        message += f"{coin_name} --> nothing to do right now... price {coin_price}"
        return (message, send, update)

    possible_profit = count_profit(coin, coin_price)  # may be negative
    message += f'{coin_name} --> TIME TO SELL stopLossPrice={coin["stopLossPrice"]} {coin_price=}\n'
    message += f"possible profit = {possible_profit}$"
    send = True
    amount = 0.0
    update = True
    status_buy = True
    if not update_storage(coin_name, coin_price, amount, status_buy, "sell"):
        logger.info(f"Something wrong with update storage")

    return (message, send, update)


ACTION = {"start": to_buy, "buy": to_buy, "sell": to_sell}


def action_with_each_coin(my_coins: dict, user_settings: dict) -> tuple:
    final_message = []
    send = False
    update = False

    for coin_name in my_coins.keys():
        coin = my_coins[coin_name]
        coin_price = get_price(coin_name)

        action_type = choose_an_action(coin["status"]["buy"])

        message, send, update = ACTION[action_type](coin, coin_price, coin_name, send, update, user_settings)

        final_message.append(message)
        logger.debug(f"{message}")

    return (send, final_message)
