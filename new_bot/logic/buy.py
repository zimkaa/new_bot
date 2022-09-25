from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from loguru import logger

from connection import trade_market

from schemas import Action, TradeStatus

from settings import (
    COEFFICIENT_WAIT_AFTER_SELL,
    COEFFICIENT_WAIT_FOR_BUY,
    ONLINE_TRADE,
    TIME_FORMAT,
    TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY,
    TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY,
)

from .actions import (
    get_klines_for_period,
    get_rounded_change,
    read_store_sell_price,
    read_store_sell_price_simple,
    read_store_sell_time,
    read_store_sell_time_simple,
    rounding_to_decimal,
    update_storage,
    update_storage_simple,
    write_state,
    write_state_simple,
)


class Buy(Action):
    def _check_top_prise(self) -> bool:
        text = f"_check_top_prise {self.coin_name}"
        logger.debug(text)
        self._get_high_low_24h_price()
        difference = (self.high_24h - self.low_24h) / 2
        self.top_price = self.low_24h + difference
        if self.top_price > self.list_klines[-1].close_price:
            text = f"self.top_price = {self.top_price}"
            logger.debug(text)
            return True
        return False

    def _get_high_low_24h_price(self):
        klines = get_klines_for_period(self.coin_name, interval="1h", limit=24)
        self.low_24h = 1000000.0
        self.high_24h = 0.0
        for kline in klines:
            if self.low_24h > kline.low_price:
                self.low_24h = kline.low_price
            if self.high_24h < kline.high_price:
                self.high_24h = kline.high_price

    def start(self) -> None:
        if self.my_state[self.coin_name]["checkTime"]:
            if self._check_next_kline():
                # text = f"Need to buy {self.coin_name}"
                # logger.error(text)
                # self._buy()
                if self._check_top_prise():
                    text = f"Need to buy {self.coin_name}"
                    logger.error(text)
                    self._buy()
                else:
                    text = (
                        f"Not buy becouse middle price is {self.top_price} now price {self.list_klines[-1].close_price}"
                    )
                    logger.error(text)
            else:
                change_persent = self._check_all_falling()
                write_state(self.coin_name, True, change_persent)
                text = f"Need to check next kline {self.coin_name}"
                logger.info(text)
        else:
            if self._check_change():
                change_persent = self._check_all_falling()
                write_state(self.coin_name, True, change_persent)
                text = f"Check_change {self.coin_name}"
                logger.info(text)
            else:
                text = f"No change to buy {self.coin_name}"
                logger.debug(text)
        self.message += text

    def _check_change(self) -> bool:
        """Checking for the trigger to buy

        :return: result of these conditions
        :rtype: bool
        """
        offset = -2
        coin_price = Decimal(self.list_klines[-1].close_price)
        sell_price = read_store_sell_price(self.coin_name)
        time_now = self.list_klines[-1].time_open
        sell_time_srt = read_store_sell_time(self.coin_name)
        sell_time = datetime.strptime(sell_time_srt, TIME_FORMAT)
        difference = time_now - sell_time
        # difference_in_hours = timedelta(hours=1)
        difference_in_hours = timedelta(minutes=20)
        if difference > difference_in_hours:
            logger.info("Ignore sell_price because passed more than 1 hour")
            sell_price = Decimal(1000000000)
        if sell_price == Decimal(0.0):
            sell_price = Decimal(1000000000)
            logger.info("Ignore sell_price. It must work only with the first start")

        change_persent = get_rounded_change(self.list_klines[offset])

        first_condition = change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY  # change_persent <= -0.002
        second_condition = coin_price < (sell_price * COEFFICIENT_WAIT_AFTER_SELL)
        third_condition = change_persent < 0

        if third_condition:
            new_offset = offset - 1
            all_change = change_persent
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                all_change += rounded_new_change
                if all_change <= -TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY:
                    logger.info(f"Kline before is falling to {rounded_new_change}")
                    logger.warning(f"All cange {all_change} {TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY=} {self.coin_name}")
                    return True
            logger.warning(f"All cange before 60 klines {all_change}")

        if first_condition and second_condition:
            change_before = get_rounded_change(self.list_klines[offset - 1])
            if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY):
                logger.debug(
                    f"Trigger to buy {self.coin_name} {change_persent=} time={self.list_klines[offset].time_open}"
                )
                return True

        if third_condition:
            logger.warning("CHEEEKK NEW CONDITIONS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            new_offset = offset - 1
            all_change = change_persent
            steps = 1
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                all_change += rounded_new_change
                if steps > 11:
                    if all_change <= -0.005:
                        logger.info(f"Kline before is falling to {rounded_new_change}")
                        logger.warning(
                            f"All cange {all_change} {TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY=} {self.coin_name}"
                        )
                        return True
                    logger.warning(f"Breack 10 klines {all_change}")
                    break
                steps += 1
            logger.warning(f"All cange before 10 klines {all_change}")
        return False

    def _check_all_falling(self) -> Optional[Decimal]:
        """Calculating falling in percent with rounding

        :return: all falling in percent
        :rtype: Decimal
        """
        offset = -2
        new_offset = offset - 1
        rounded_change = get_rounded_change(self.list_klines[offset])
        if rounded_change < 0:
            all_change = rounded_change
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                if rounded_new_change >= 0:
                    break
                all_change += rounded_new_change
            logger.warning(f"All falling {all_change}")
            return all_change
        return None

    def _buy(self) -> None:
        """Execute buy. Write to history and send a command to the stock exchange
        :param user_settings: settings to write
        :type user_settings: dict
        """
        logger.error("Buy now -----")
        time_open = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
        logger.error(f"time_open {time_open}")

        coin_price = self.list_klines[-1].close_price
        if self.coin_name == "BTC":
            amount = 0.00246
        else:
            amount = 6.0
        status_buy = False
        type_operation = TradeStatus.BUY

        action = update_storage(
            self.coin_name, coin_price, amount, status_buy, type_operation, time_open, self.user_settings
        )
        if action:
            logger.debug("Update_storage action in buy")
        else:
            logger.debug("Trouble with update_storage")

        if ONLINE_TRADE:
            if self.coin_name == "BTC":
                trade_market(self.coin_name, type_operation, amount)

        write_state(self.coin_name, False, Decimal(0))

    def _check_next_kline(self) -> bool:
        """Check need to buy now or wait

        :return: result of these conditions
        :rtype: bool
        """
        logger.info("Check_next_kline")
        offset = -2
        item = self.list_klines[offset]
        change = get_rounded_change(item)
        rounded_fall = rounding_to_decimal(self.my_state[self.coin_name]["fall"])
        if change >= COEFFICIENT_WAIT_FOR_BUY and change < abs(rounded_fall / 2):
            logger.info(f"{self.list_klines[offset].close_price=}")
            return True
        if self._check_old_kline(offset, change):
            return True
        return False

    def _check_old_kline(self, offset: int, change: Decimal) -> bool:
        """Check old kline for growing up to COEFFICIENT_WAIT_FOR_BUY

        :param offset: start Klline to check
        :type offset: int
        :param change: change before
        :type change: Decimal
        :return: result of these conditions
        :rtype: bool
        """
        new_offset = offset - 1
        rounded_change = rounding_to_decimal(change)
        all_change = rounded_change
        for kline in self.list_klines[new_offset::-1]:
            rounded_new_change = get_rounded_change(kline)
            all_change += rounded_new_change
            if all_change >= COEFFICIENT_WAIT_FOR_BUY:
                logger.info("Old kline is grow up to trigger")
                logger.warning(f"All cange {all_change}")
                return True
            elif rounded_new_change < 0:
                logger.info("Fall not enough to buy")
                break
        return False


class BuySimple(Action):
    def start(self) -> None:
        if self.my_state[self.coin_name]["checkTime"]:
            if self._check_next_kline():
                if self._check_top_prise():
                    text = f"Need to buy {self.coin_name}"
                    logger.error(text)
                    self._buy()
                else:
                    text = (
                        f"Not buy becouse middle price is {self.top_price} now price {self.list_klines[-1].close_price}"
                    )
                    logger.error(text)
            else:
                change_persent = self._check_all_falling()
                write_state_simple(self.coin_name, True, change_persent)
                text = f"Need to check next kline {self.coin_name}"
                logger.info(text)
        else:
            if self._check_change():
                change_persent = self._check_all_falling()
                write_state_simple(self.coin_name, True, change_persent)
                text = f"Check_change {self.coin_name}"
                logger.info(text)
            else:
                text = f"No change to buy {self.coin_name}"
                logger.debug(text)
        self.message += text

    def _check_top_prise(self) -> bool:
        text = f"_check_top_prise {self.coin_name}"
        logger.debug(text)
        self._get_high_low_24h_price()
        difference = (self.high_24h - self.low_24h) / 2
        self.top_price = self.low_24h + difference
        if self.top_price > self.list_klines[-1].close_price:
            text = f"self.top_price = {self.top_price}"
            logger.debug(text)
            return True
        return False

    def _get_high_low_24h_price(self):
        klines = get_klines_for_period(self.coin_name, interval="1h", limit=24)
        self.low_24h = 1000000.0
        self.high_24h = 0.0
        for kline in klines:
            if self.low_24h > kline.low_price:
                self.low_24h = kline.low_price
            if self.high_24h < kline.high_price:
                self.high_24h = kline.high_price

    def _check_change(self) -> bool:
        """Checking for the trigger to buy

        :return: result of these conditions
        :rtype: bool
        """
        offset = -2
        coin_price = Decimal(self.list_klines[-1].close_price)
        sell_price = read_store_sell_price_simple(self.coin_name)
        time_now = self.list_klines[-1].time_open
        sell_time_srt = read_store_sell_time_simple(self.coin_name)
        sell_time = datetime.strptime(sell_time_srt, TIME_FORMAT)
        difference = time_now - sell_time
        # difference_in_hours = timedelta(hours=1)
        difference_in_hours = timedelta(minutes=20)
        if difference > difference_in_hours:
            logger.info("Ignore sell_price because passed more than 1 hour")
            sell_price = Decimal(1000000000)
        if sell_price == Decimal(0.0):
            sell_price = Decimal(1000000000)
            logger.info("Ignore sell_price. It must work only with the first start")

        change_persent = get_rounded_change(self.list_klines[offset])

        first_condition = change_persent <= -TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY  # change_persent <= -0.002
        second_condition = coin_price < (sell_price * COEFFICIENT_WAIT_AFTER_SELL)
        third_condition = change_persent < 0

        if third_condition:
            new_offset = offset - 1
            all_change = change_persent
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                all_change += rounded_new_change
                if all_change <= -TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY:
                    logger.info(f"Kline before is falling to {rounded_new_change}")
                    logger.warning(f"All cange {all_change} {TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY=} {self.coin_name}")
                    logger.debug(
                        f"Trigger to buy {self.coin_name} {change_persent=} time={self.list_klines[offset].time_open}"
                    )
                    return True
            logger.warning(f"All cange before 60 klines {all_change}")

        if first_condition and second_condition:
            change_before = get_rounded_change(self.list_klines[offset - 1])
            if change_before < abs(change_persent + TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY):
                logger.debug(
                    f"Trigger to buy {self.coin_name} {change_persent=} time={self.list_klines[offset].time_open}"
                )
                return True

        if third_condition:
            logger.warning("CHEEEKK NEW CONDITIONS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            new_offset = offset - 1
            all_change = change_persent
            steps = 1
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                all_change += rounded_new_change
                if steps > 11:
                    if all_change <= -0.005:
                        logger.info(f"Kline before is falling to {rounded_new_change}")
                        logger.warning(
                            f"All cange {all_change} {TRIGGER_PRICE_FALL_PER_PERIOD_FOR_BUY=} {self.coin_name}"
                        )
                        logger.debug(f"Trigger to buy {self.coin_name} time={self.list_klines[offset].time_open}")
                        return True
                    logger.warning(f"Breack 10 klines {all_change}")
                    break
                steps += 1
            logger.warning(f"All cange before 10 klines {all_change}")
        return False

    def _check_all_falling(self) -> Optional[Decimal]:
        """Calculating falling in percent with rounding

        :return: all falling in percent
        :rtype: Decimal
        """
        offset = -2
        new_offset = offset - 1
        rounded_change = get_rounded_change(self.list_klines[offset])
        if rounded_change < 0:
            all_change = rounded_change
            for kline in self.list_klines[new_offset::-1]:
                rounded_new_change = get_rounded_change(kline)
                if rounded_new_change >= 0:
                    break
                all_change += rounded_new_change
            logger.warning(f"All falling {all_change}")
            return all_change
        return None

    def _buy(self) -> None:
        """Execute buy. Write to history and send a command to the stock exchange
        :param user_settings: settings to write
        :type user_settings: dict
        """
        logger.error("Buy now -----")
        time_open = self.list_klines[-1].time_open.strftime(TIME_FORMAT)
        logger.error(f"time_open {time_open}")

        coin_price = self.list_klines[-1].close_price
        if self.coin_name == "BTC":
            amount = 0.00246
        else:
            amount = 6.0
        status_buy = False
        type_operation = TradeStatus.BUY

        action = update_storage_simple(
            self.coin_name, coin_price, amount, status_buy, type_operation, time_open, self.user_settings
        )
        if action:
            logger.debug("Update_storage action in buy")
        else:
            logger.debug("Trouble with update_storage")

        if ONLINE_TRADE:
            if self.coin_name == "BTC":
                trade_market(self.coin_name, type_operation, amount)

        write_state_simple(self.coin_name, False, Decimal(0))

    def _check_next_kline(self) -> bool:
        """Check need to buy now or wait

        :return: result of these conditions
        :rtype: bool
        """
        logger.info("Check_next_kline")
        offset = -2
        new_offset = offset - 1
        item = self.list_klines[offset]
        change = get_rounded_change(item)
        rounded_fall = rounding_to_decimal(self.my_state[self.coin_name]["fall"])
        if change >= COEFFICIENT_WAIT_FOR_BUY and change < abs(rounded_fall / 2):
            logger.critical(f"{self.list_klines[offset].close_price=}")
            new_item = self.list_klines[new_offset]
            before_change = get_rounded_change(new_item)
            if before_change <= 0:
                get_rounded_change(item)
                logger.critical(f"{self.list_klines[offset].close_price=} <= 0")
                return False
            return True
        if self._check_old_kline(offset, change):
            return True
        return False

    def _check_old_kline(self, offset: int, change: Decimal) -> bool:
        """Check old kline for growing up to COEFFICIENT_WAIT_FOR_BUY

        :param offset: start Klline to check
        :type offset: int
        :param change: change before
        :type change: Decimal
        :return: result of these conditions
        :rtype: bool
        """
        new_offset = offset - 1
        rounded_change = rounding_to_decimal(change)
        all_change = rounded_change
        for kline in self.list_klines[new_offset::-1]:
            rounded_new_change = get_rounded_change(kline)
            all_change += rounded_new_change
            if all_change >= COEFFICIENT_WAIT_FOR_BUY:
                logger.info("Old kline is grow up to trigger")
                logger.warning(f"All cange {all_change}")
                return True
            elif rounded_new_change < 0:
                logger.info("Fall not enough to buy")
                break
        return False
