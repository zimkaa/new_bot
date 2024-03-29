import sys
from datetime import datetime
from enum import Enum, unique
from typing import List, Optional

import attr

from pydantic import BaseModel, Extra, Field, confloat


if sys.version_info >= (3, 10):
    from typing import TypeAlias  # it's for 3.10 Python

    not_negative_float: TypeAlias = confloat(strict=True, ge=0.0)  # it's for 3.10 Python
else:
    not_negative_float = confloat(strict=True, ge=0.0)  # it's for 3.8 Python


def str_to_datetime(item: str) -> datetime:
    return datetime.fromtimestamp(float(item) / 1e3)


@unique
class TradeStatus(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@attr.s
class Coin:
    amount: float = attr.ib(converter=float)


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


class Settings(BaseModel, extra=Extra.forbid):
    raise_up_to: not_negative_float = Field(alias="raiseUpTo")
    down_to: not_negative_float = Field(alias="downTo")
    stop_loss: not_negative_float = Field(alias="stopLoss")


class Ratios(BaseModel, extra=Extra.forbid):
    up_to_ratio: not_negative_float
    down_to_ratio: not_negative_float
    stop_loss_ratio: not_negative_float
    min_price_ratio: not_negative_float


class Store(BaseModel, extra=Extra.forbid):
    coin_name: str


class ByInfo(BaseModel, extra=Extra.forbid):
    time: str
    price: not_negative_float


class SellInfo(BaseModel, extra=Extra.forbid):
    time: str
    price: not_negative_float
    stop_loss_reason: bool = Field(alias="stopLossReason")
    profit: float


class History(BaseModel, extra=Extra.forbid):
    BUY: List[Optional[ByInfo]]
    SELL: List[Optional[SellInfo]]


class Status(BaseModel, extra=Extra.forbid):
    buy: bool


# class CoinInfo(BaseModel, extra=Extra.forbid):
class CoinInfo(BaseModel):
    amount: not_negative_float
    balanse: float
    buy_price: not_negative_float = Field(alias="buyPrice")
    buy_time: str = Field(alias="buyTime")
    current_price: not_negative_float = Field(alias="currentPrice")
    desired_sell_price: not_negative_float = Field(alias="desiredPriceFall")
    history: History
    sell_price: not_negative_float = Field(alias="sellPrice")
    sell_time: str = Field(alias="sellTime")
    status: Status
    stop_loss_price: not_negative_float = Field(alias="stopLossPrice")
