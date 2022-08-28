from decimal import Decimal
from typing import List

from loguru import logger

from connection import trade_market

from schemas import Action, Kline, TradeStatus

from settings import (
    COEFFICIENT_DOWN_TO,
    COEFFICIENT_RISE_UP_TO,
    TIME_FORMAT,
    ONLINE_TRADE,
)

from .actions import (
    get_rounded_change,
    reed_store,
    rounding_to_float,
    update_stop_loss_price,
    update_storage,
)


class Sell(Action):
    # def __init__(self, user_settings: dict, coin_name: str, my_state: dict, list_klines: List[Kline]) -> None:
    #     """
    #     :param user_settings: settings to write
    #     :type user_settings: dict
    #     :param coin_name: coin name (tiker)
    #     :type coin_name: str
    #     :param my_state: statement dictionary
    #     :type my_state: dict
    #     :param list_klines: all Klines
    #     :type list_klines: List[Kline]
    #     """
    #     self.user_settings = user_settings
    #     self.coin_name = coin_name
    #     self.my_state = my_state
    #     self.list_klines = list_klines
    #     self.send = True
    #     self.message = ""

    def start(self) -> None:
        if self._check_stop_loss():
            stop_loss_reason = True
            coin_price = self.list_klines[-1].close_price
            if self.coin_name == "BTC":
                amount = 0.00246
            else:
                amount = 6.0
            status_buy = True
            type_operation = TradeStatus.SELL
            time_sell = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
            action = update_storage(
                self.coin_name,
                coin_price,
                amount,
                status_buy,
                type_operation,
                time_sell,
                self.user_settings,
                stop_loss_reason,
            )
            if action:
                logger.debug("Update_storage action in check_fall")
            else:
                logger.warning("Trouble with update_storage")

            if ONLINE_TRADE:
                if self.coin_name == "BTC":
                    trade_market(self.coin_name, type_operation, amount)

            text = f"Need to sell {self.coin_name} time_open {time_sell}"
            logger.error(text)

        else:
            if self._should_change_stop_loss():
                text = f"WE UPDATE STOP LOSS PRICE {self.coin_name}"
                logger.debug(text)
            else:
                last_kline_time = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
                text = f"Not time to sell yet {self.coin_name} {last_kline_time}"
                logger.debug(text)

        self.message += text

    def _should_change_stop_loss(self) -> bool:
        """Should change stop_loss or not"""
        kline_offset = -2
        item = self.list_klines[kline_offset]
        logger.info(f"Start check_fall close_price={item.close_price} time_open={item.time_open}")

        # change = search_changes(item)
        # rounded_change = rounding_to_decimal(change)
        rounded_change = get_rounded_change(item)
        if rounded_change > 0:
            logger.info(f"We have a grow {self.coin_name} up to {rounded_change}")
        else:
            logger.info(f"We have a fall {self.coin_name} down to {rounded_change}")
        buy_price = Decimal(reed_store(self.coin_name)["buyPrice"])
        coin_info = reed_store(self.coin_name)
        stop_loss_price = Decimal(coin_info["stopLossPrice"])
        new_stop_loss = Decimal(item.low_price) * COEFFICIENT_DOWN_TO
        if item.low_price > (buy_price * COEFFICIENT_RISE_UP_TO) and new_stop_loss > stop_loss_price:
            action = update_stop_loss_price(self.coin_name, rounding_to_float(new_stop_loss))
            if action:
                logger.debug("update_stop_loss_price action in check_fall")
            else:
                logger.warning("Trouble with update_stop_loss_price")
            logger.debug(f"WE UPDATE STOP LOSS PRICE {self.coin_name} to {new_stop_loss}")
            logger.warning(f"NOW PRICE to {self.list_klines[-1].close_price}")
            return True
        return False

    def _check_stop_loss(self) -> bool:
        """_summary_

        :return: result of these conditions
        :rtype: bool
        """
        kline_offset = -2
        close_price = Decimal(self.list_klines[kline_offset].close_price)

        coin_info = reed_store(self.coin_name)
        stop_loss_price = coin_info["stopLossPrice"]

        if stop_loss_price > close_price:
            logger.warning(f"Stoploss sell {self.coin_name} price now {self.list_klines[-1].close_price}")
            logger.error(f"We need to sell now {self.coin_name} {self.list_klines[-1].time_open}")
            return True
        return False

    # def need_send_message(self) -> bool:
    #     return self.send

    # def get_message_text(self) -> str:
    #     return self.message
