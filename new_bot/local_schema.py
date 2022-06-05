from typing import List
import json

from pydantic import BaseModel, Extra, ValidationError, Field, confloat


not_negative_float = confloat(strict=True, ge=0.0)


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


class History(BaseModel, extra=Extra.forbid):
    buy: List[not_negative_float]
    sell: List[not_negative_float]


class Status(BaseModel, extra=Extra.forbid):
    buy: bool


# class CoinInfo(BaseModel, extra=Extra.forbid):
class CoinInfo(BaseModel):
    amount: not_negative_float
    buy_price: not_negative_float = Field(alias="buyPrice")
    current_price: not_negative_float = Field(alias="currentPrice")
    desired_sell_price: not_negative_float = Field(alias="desiredPriceFall")
    history: History
    status: Status
    stop_loss_price: not_negative_float = Field(alias="stopLossPrice")


if __name__ == "__main__":
    with open("storage copy.json", "r", encoding="utf8") as settings_file:

        settings_data = json.loads(settings_file.read())
        name_info_dict = {}
        for key, value in settings_data.items():
            try:
                data = CoinInfo.parse_obj(value)
                name_info_dict[key] = data.dict()
            except ValidationError as e:
                raise TypeError(f"'{key}' does not match the schema {e.json()}")
        # print(name_info_dict)
        print(f"{CoinInfo.__name__}")
        # settings_data = CoinInfo.parse_raw(settings_file.read())
        # print(settings_data.dict())
