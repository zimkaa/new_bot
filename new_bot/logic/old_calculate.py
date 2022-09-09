from typing import Dict, Tuple
from loguru import logger

# from connection import client

from schemas import TradeStatus

# from .not_used_buy import to_buy

from .buy import Buy

# from .not_used_sell import to_sell

from .sell import Sell

from .actions import get_klines_for_period

from schemas import Action


# def get_price(coin_name: str) -> float:
#     """Gets the price of the coin

#     :param coin_name: coin name (tiker)
#     :type coin_name: str
#     :return: coin price
#     :rtype: float
#     """
#     trading_pair = f"{coin_name}USDT"
#     # return float(client.avg_price(trading_pair)["price"])
#     price = client.ticker_price(trading_pair)["price"]
#     # logger.error(f"{price=} type {type(price)}")
#     # logger.error(f"{float(price)} type {type(float(price))}")
#     return float(price)


def choose_an_action(status: bool) -> str:
    """
    Choose the next action

    :param status: status, defaults to None
    :type status: bool, optional
    :return: name of the doing
    :rtype: str
    """
    if status:
        return TradeStatus.BUY
    return TradeStatus.SELL


# ACTION = {"BUY": to_buy, "SELL": to_sell}


ACTION: Dict[str, Action] = {"BUY": Buy, "SELL": Sell}


# def action_with_each_coin(my_coins: dict, user_settings: dict, my_state: dict) -> Tuple[bool, list[str]]:
#     final_message = []
#     send = False
#     # update = False

#     for coin_name in my_coins.keys():
#         coin = my_coins[coin_name]
#         # coin_price = get_price(coin_name)

#         action_type = choose_an_action(coin["status"]["buy"])

#         # message, send, update = ACTION[action_type](coin, coin_price, coin_name, send, update, user_settings)
#         message, send = ACTION[action_type](user_settings, coin_name, my_state)
#         # list_klines = get_klines_for_period(coin_name, limit=60)

#         final_message.append(message)
#         logger.debug(f"{message}")

#     return (send, final_message)


def action_with_each_coin(my_coins: dict, user_settings: dict, my_state: dict) -> Tuple[bool, list[str]]:
    final_message = []
    send = False
    # update = False

    for coin_name in my_coins.keys():
        coin = my_coins[coin_name]
        # coin_price = get_price(coin_name)

        action_type = choose_an_action(coin["status"]["buy"])

        # message, send, update = ACTION[action_type](coin, coin_price, coin_name, send, update, user_settings)

        list_klines = get_klines_for_period(coin_name, limit=60)
        action: Action = ACTION[action_type](user_settings, coin_name, my_state, list_klines)

        action.start()

        send = action.need_send_message()

        message = action.get_message_text()

        final_message.append(message)
        logger.debug(f"{message}")

    return (send, final_message)
