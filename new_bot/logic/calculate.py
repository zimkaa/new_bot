from typing import Dict, Tuple, List

from loguru import logger

from schemas import TradeStatus

from .buy import Buy
from .buy import BuySimple

from .sell import Sell
from .sell import SellSimple

from .actions import get_klines_for_period

from schemas import Action


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


ACTION: Dict[str, Action] = {"BUY": Buy, "SELL": Sell}


def action_with_each_coin(my_coins: dict, user_settings: dict, my_state: dict) -> Tuple[bool, List[str]]:
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


ACTION_SIMPLE: Dict[str, Action] = {"BUY": BuySimple, "SELL": SellSimple}


def action_with_each_coin_simple(my_coins: dict, user_settings: dict, my_state: dict) -> Tuple[bool, List[str]]:
    final_message = []
    send = False
    # update = False

    for coin_name in my_coins.keys():
        coin = my_coins[coin_name]
        # coin_price = get_price(coin_name)

        action_type = choose_an_action(coin["status"]["buy"])

        # message, send, update = ACTION[action_type](coin, coin_price, coin_name, send, update, user_settings)

        list_klines = get_klines_for_period(coin_name, limit=60)
        action: Action = ACTION_SIMPLE[action_type](user_settings, coin_name, my_state, list_klines)

        action.start()

        send = action.need_send_message()

        message = action.get_message_text()

        final_message.append(message)
        logger.debug(f"{message}")

    return (send, final_message)
