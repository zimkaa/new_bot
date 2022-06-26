import json
from decimal import Decimal, ROUND_DOWN
from typing import List, Optional, Union

from loguru import logger

from connection import client

from schemas import CoinInfo, Kline, TradeStatus, ValidationError

from settings import COEFFICIENT_FOR_PROFIT, ROUNDING


def get_klines_for_period(coin_name: str, *, interval: str = "1m", limit: int = 240) -> List[Kline]:
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
    if limit < 2:
        limit = 2
    trading_pair = f"{coin_name}USDT"
    prices = client.klines(trading_pair, interval, limit=limit)
    klines_list = [Kline(*item) for item in prices]
    return klines_list


def reed_store(coin_name: str) -> dict:
    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())
    return my_coins[coin_name]


def read_store_buy_price(coin_name: str) -> Decimal:
    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())
    return Decimal(my_coins[coin_name]["buyPrice"])


def read_store_sell_price(coin_name: str) -> Decimal:
    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())
    return Decimal(my_coins[coin_name]["sellPrice"])


def read_store_stop_loss_price(coin_name: str) -> Decimal:
    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())
    return Decimal(my_coins[coin_name]["stopLossPrice"])


def read_store_sell_time(coin_name: str) -> str:
    with open("storage.json", "r", encoding="utf8") as my_coins_data:
        my_coins = json.loads(my_coins_data.read())
    return my_coins[coin_name]["sellTime"]


def write_state(coin_name: str, data: int):
    with open("state.json", "r+", encoding="utf8") as my_coins_data:
        my_state = json.loads(my_coins_data.read())
        my_state[coin_name]["checkTime"] = data
        my_coins_data.seek(0)
        my_coins_data.write(json.dumps(my_state, sort_keys=True, indent=2))
        my_coins_data.truncate()


def _count_profit(coin: dict, current_price: float) -> float:
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
    type_operation: TradeStatus,
    time: str,
    user_settings: Optional[dict] = None,
    stop_loss_reason: bool = False,
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
            history_dict = {"time": time, "price": coin_price}
            # if type_operation == TradeStatus.BUY.value:
            if type_operation == TradeStatus.BUY:
                my_coins[coin_name]["buyPrice"] = coin_price
                my_coins[coin_name]["buyTime"] = time
                my_coins[coin_name]["sellPrice"] = 0.0
                if user_settings:
                    stop_loss_price = coin_price * user_settings["stop_loss_ratio"]
                else:
                    logger.warning("Trouble wuth writing stop_loss_ratio")
                my_coins[coin_name]["stopLossPrice"] = stop_loss_price
                # logger.info(f"Write buyPrice = {coin_price}")
                # logger.info(f"Write stop_loss_price = {stop_loss_price}")
                # logger.info(f"Write stop_loss_ratio = {user_settings['stop_loss_ratio']}")
            else:
                possible_profit = _count_profit(my_coins[coin_name], coin_price)
                my_coins[coin_name]["buyPrice"] = 0.0
                my_coins[coin_name]["sellPrice"] = coin_price
                my_coins[coin_name]["sellTime"] = time
                my_coins[coin_name]["stopLossPrice"] = 0.0
                my_coins[coin_name]["balanse"] += possible_profit
                history_dict["stopLossReason"] = stop_loss_reason
                history_dict["profit"] = possible_profit
            # my_coins[coin_name]['currentPrice'] = coin_price
            my_coins[coin_name]["history"][type_operation].append(history_dict)
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
        logger.debug(f"ERROR WITH update_storage {err=}")
        return False


def search_changes(item: Kline) -> Decimal:
    change = 1 - item.open_price / item.close_price
    return Decimal(change)


def rounding_to_decimal(some_value: Union[float, Decimal]) -> Decimal:
    if isinstance(some_value, float):
        rouded_value = Decimal(some_value)
    else:
        rouded_value = some_value
    return rouded_value.quantize(Decimal(ROUNDING), rounding=ROUND_DOWN)


def rounding_to_float(some_value: Decimal) -> float:
    rounded = some_value.quantize(Decimal(ROUNDING), rounding=ROUND_DOWN)
    return float(rounded)


def update_stop_loss_price(coin_name: str, stop_loss_price: float) -> bool:
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

    except Exception as err:
        logger.warning(f"Trouble {err=}")
        return False


def set_order_with_stop_loss(
    coin_name: str,
    price_stop_loss: float,
    old_price_stop_loss: float,
    *,
    amount: float = None,
) -> bool:
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
        return True
    except Exception as err:
        logger.error(f"Something rong with query stop loss \n {err}")
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


def get_max_price_new(list_of_price: List[Kline]) -> float:
    """Get maximum price

    :param list_of_price: list of prices
    :type list_of_price: list[Price]
    :return: maximum price
    :rtype: float
    """
    max_price = max([item.high_price for item in list_of_price])
    return max_price


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
