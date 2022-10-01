from decimal import Decimal

from loguru import logger

from connection import trade_market, trade_limit, get_price_now

from schemas import Action, TradeStatus

from settings import (
    COEFFICIENT_DOWN_TO,
    COEFFICIENT_RISE_UP_TO,
    TIME_FORMAT,
    ONLINE_TRADE,
)

from .actions import (
    get_rounded_change,
    reed_store,
    reed_store_simple,
    rounding_to_float,
    update_stop_loss_price,
    update_storage,
    update_storage_simple,
)


class SellSimple(Action):
    def start(self) -> None:
        if self._check_stop_loss():
            stop_loss_reason = True
            coin_price = self.list_klines[-1].close_price
            if self.coin_name == "BTC":
                amount = 0.00244
            else:
                amount = 5.8
            status_buy = True
            type_operation = TradeStatus.SELL
            time_sell = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
            action = update_storage_simple(
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
                    stop_loss_price = self.coin_info["stopLossPrice"]
                    print(f"type{type(stop_loss_price)}  {stop_loss_price=}")
                    text = f"type{type(stop_loss_price)}  {stop_loss_price=}"
                    logger.error(text)
                    text = f"type{type(self.coin_name)}  {self.coin_name=}"
                    logger.error(text)
                    text = f"type{type(type_operation)}  {type_operation=}"
                    logger.error(text)
                    text = f"type{type(amount)}  {amount=}"
                    logger.error(text)
                    trade_limit(self.coin_name, type_operation, amount, float(stop_loss_price))

            text = f"Need to sell {self.coin_name} time_open {time_sell}"
            logger.error(text)

        else:
            last_kline_time = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
            text = f"Not time to sell yet {self.coin_name} {last_kline_time}"
            logger.debug(text)

        self.message += text

    def _check_stop_loss(self) -> bool:
        """_summary_

        :return: result of these conditions
        :rtype: bool
        """
        self.coin_info = reed_store_simple(self.coin_name)
        stop_loss_price = self.coin_info["stopLossPrice"]
        price = get_price_now(self.coin_name)
        if price > stop_loss_price:
            logger.warning(f"Stoploss sell {self.coin_name} price now {price}")
            logger.error(f"We need to sell now {self.coin_name} {self.list_klines[-1].time_open}")
            return True
        return False


class Sell(Action):
    def start(self) -> None:
        if self._check_stop_loss():
            stop_loss_reason = True
            coin_price = self.list_klines[-1].close_price
            if self.coin_name == "BTC":
                amount = 0.00244
            else:
                amount = 5.8
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
        coin_info = reed_store(self.coin_name)
        buy_price = Decimal(coin_info["buyPrice"])
        stop_loss_price = Decimal(coin_info["stopLossPrice"])
        new_stop_loss = Decimal(item.low_price) * COEFFICIENT_DOWN_TO

        new_stop_loss2 = Decimal(item.low_price) * Decimal(1 - 0.2 / 100)

        if item.low_price > (buy_price * Decimal(1 + 1 / 100)) and new_stop_loss2 > stop_loss_price:
            action = update_stop_loss_price(self.coin_name, rounding_to_float(new_stop_loss2))
            if action:
                logger.debug("update_stop_loss_price action item.low_price > buy_price * 1,01")
            else:
                logger.warning("Trouble with update_stop_loss_price")
            logger.debug(f"WE UPDATE STOP LOSS PRICE {self.coin_name} to {new_stop_loss2}")
            logger.warning(f"NOW PRICE to {self.list_klines[-1].close_price}")
            return True
        else:
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
