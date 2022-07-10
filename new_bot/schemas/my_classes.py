from abc import ABC, abstractmethod
from typing import List

from .api_schemas import Kline


class Action(ABC):
    def __init__(self, user_settings: dict, coin_name: str, my_state: dict, list_klines: List[Kline]) -> None:
        """
        :param user_settings: settings to write
        :type user_settings: dict
        :param coin_name: coin name (tiker)
        :type coin_name: str
        :param my_state: statement dictionary
        :type my_state: dict
        :param list_klines: all Klines
        :type list_klines: List[Kline]
        """
        self.user_settings = user_settings
        self.coin_name = coin_name
        self.my_state = my_state
        self.list_klines = list_klines
        self.send = True
        self.message = ""

    @abstractmethod
    def start(self) -> None:
        """Start calculating"""
        pass

    def need_send_message(self) -> bool:
        return self.send

    def get_message_text(self) -> str:
        return self.message
