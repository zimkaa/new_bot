from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, Field

from binance.spot import Spot as Client


BINANCE_KEY = "A7YsQZKE87IlT4gf20w8QSVtCw1vxwBAWz8f2DWgeviReiEGx5JJh70lXNGBLFKc"

BINANCE_SECRET = "JpNwrxgWonkEXWrVzIsoXVdAhSRQSSZJNslxF83aOdLDEHwRMkrDxSzCc0AVbJXb"

client = Client(key=BINANCE_KEY, secret=BINANCE_SECRET)


percent: TypeAlias = Decimal

tiker_list = ["BTC", "NEAR", "ETH", "ADA"]


class Tiker(Enum):
    BTC = "BTC"
    NEAR = "NEAR"
    ETH = "ETH"
    ADA = "ADA"
    USDT = "USDT"


class Price(BaseModel):
    symbol: str
    price: Decimal


class Asset(BaseModel):
    asset: str


class BalanceItem(Asset):
    free: Decimal
    locked: Decimal


class Account(BaseModel):
    maker_commission: int = Field(alias="makerCommission")
    taker_commission: int = Field(alias="takerCommission")
    buyer_commission: int = Field(alias="buyerCommission")
    seller_commission: int = Field(alias="sellerCommission")
    can_trade: bool = Field(alias="canTrade")
    can_withdraw: bool = Field(alias="canWithdraw")
    can_deposit: bool = Field(alias="canDeposit")
    update_time: int = Field(alias="updateTime")
    account_type: str = Field(alias="accountType")
    balances: list[BalanceItem]
    permissions: list[str]


class PortfolioSettings(Asset):
    amount: Decimal = Decimal(0.0)
    now_price: Decimal = Decimal(0.0)
    purchase_price: Decimal = Decimal(0.0)
    now_portfolio_share: Decimal = Decimal(0.0)
    need_portfolio_share: Decimal = Decimal(0.0)
    summ_in_usdt: Decimal = Decimal(0.0)


class Element(BaseModel):
    amount: Decimal = Decimal(0.0)
    price: Decimal = Decimal(0.0)
    portfolio_share: Decimal = Decimal(0.0)


class Portfolio(ABC):
    def __init__(self, portfolio_settings: list[PortfolioSettings], max_deviation: percent) -> None:
        """
        :param portfolio_settings: settings
        :type portfolio_settings: dict
        """
        self.initial_portfolio_settings = portfolio_settings
        self.tikers = list()
        for item in portfolio_settings:
            setattr(self, item.asset, item)
            self.tikers.append(item.asset)
            # if not item.asset == "USDT":
            #     setattr(self, item.asset, item)
            #     self.tikers.append(item.asset)
            # else:
            #     self.money_to_buy = item.amount

        self.trade_simbols = [f"{simbol}USDT" for simbol in self.tikers]
        self.trade_simbols.remove("USDTUSDT")
        # self.trade_simbols = [f"{simbol}USDT" for simbol in self.tikers]
        self.max_deviation = max_deviation
        self.real_percent: dict[str, Decimal] = dict()
        self.price: dict[str, Decimal] = dict()
        self.list_summ_of_portfolio: list[Decimal] = list()

    @abstractmethod
    def start(self):
        """Start calculating"""
        pass

    def get_prices(self):
        prices = client.ticker_price(symbols=self.trade_simbols)
        for element in prices:
            if element["symbol"] in self.trade_simbols:
                self.price[element["symbol"]] = Decimal(element["price"])
        # self.price["USDTUSDT"] = Decimal(1)

    def set_actual_portfolio_structure(self, balances: list[BalanceItem]):
        self.get_prices()
        self.balances = balances
        for item in balances:
            try:
                element: PortfolioSettings = getattr(self, item.asset)
                amount = item.free + item.locked
                # self.real_percent[item.asset] = amount * price
                if not item.asset == "USDT":
                    summ_of_item = amount * self.price[f"{item.asset}USDT"]
                else:
                    # summ_of_item = amount
                    element.summ_in_usdt = amount
                    element.now_price = Decimal(1)
                    self.list_summ_of_portfolio.append(amount)
                    continue
                # summ_of_item = amount * self.price[f"{item.asset}USDT"]
                self.real_percent[item.asset] = summ_of_item
                # element = Element(amount=amount, price=self.price[f"{item.asset}USDT"])
                element.now_price = self.price[f"{item.asset}USDT"]
                element.summ_in_usdt = summ_of_item
                element.amount = amount
                element.purchase_price = self.price[f"{item.asset}USDT"]
                self.list_summ_of_portfolio.append(summ_of_item)
            except AttributeError:
                print(f"We have AttributeError!!! No {item.asset} in self portfolio")
        return self.real_percent

    def get_all_summ(self) -> Decimal:
        self.summ = Decimal(0)
        for element in self.list_summ_of_portfolio:
            self.summ += element
        return self.summ

    def get_percent(self) -> list:
        all_summ = self.get_all_summ()
        print(f"{all_summ=}")
        answer = []
        for item in self.balances:
            try:
                element: PortfolioSettings = getattr(self, item.asset)
                amount = item.free + item.locked
                if item.asset == "USDT":
                    need_summ_in_usdt = all_summ * (element.need_portfolio_share / 100)
                    summ_in_usdt_more = need_summ_in_usdt * (Decimal(1) + self.max_deviation / 100)
                    summ_in_usdt_less = need_summ_in_usdt * (Decimal(1) - self.max_deviation / 100)
                    if element.summ_in_usdt > summ_in_usdt_more:
                        sell_amount = element.summ_in_usdt - need_summ_in_usdt
                        percent_of_element_now = sell_amount * 100 / element.summ_in_usdt
                        sell_amount2 = sell_amount / element.now_price
                        answer.append(
                            f"{item.asset} is more then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} > need={summ_in_usdt_more} "
                            f"{sell_amount2=} {percent_of_element_now=}"
                        )
                    elif element.summ_in_usdt < summ_in_usdt_less:
                        buy_amount = need_summ_in_usdt - element.summ_in_usdt
                        percent_of_element_now = buy_amount * 100 / element.summ_in_usdt
                        buy_amount2 = buy_amount / element.now_price
                        answer.append(
                            f"{item.asset} is less then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} < need={summ_in_usdt_less} "
                            f"{buy_amount2=} {percent_of_element_now=}"
                        )
                elif not amount == Decimal(0):
                    need_summ_in_usdt = all_summ * (element.need_portfolio_share / 100)
                    summ_in_usdt_more = need_summ_in_usdt * (Decimal(1) + self.max_deviation / 100)
                    summ_in_usdt_less = need_summ_in_usdt * (Decimal(1) - self.max_deviation / 100)
                    if element.summ_in_usdt > summ_in_usdt_more:
                        sell_amount = element.summ_in_usdt - need_summ_in_usdt
                        percent_of_element_now = sell_amount * 100 / element.summ_in_usdt
                        sell_amount2 = sell_amount / element.now_price
                        answer.append(
                            f"{item.asset} is more then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} > need={summ_in_usdt_more} "
                            f"{sell_amount2=} {percent_of_element_now=}"
                        )
                    elif element.summ_in_usdt < summ_in_usdt_less:
                        buy_amount = need_summ_in_usdt - element.summ_in_usdt
                        percent_of_element_now = buy_amount * 100 / element.summ_in_usdt
                        buy_amount2 = buy_amount / element.now_price
                        answer.append(
                            f"{item.asset} is less then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} < need={summ_in_usdt_less} "
                            f"{buy_amount2=} {percent_of_element_now=}"
                        )
                else:
                    print(f"{item.asset} amount == 0")
            except AttributeError:
                print(f"We have AttributeError!!! No {item.asset} in self portfolio")
        return answer

    def get_all_initial_summ(self) -> Decimal:
        self.all_initial_summ = Decimal(0)
        for element in self.list_summ_of_portfolio:
            self.all_initial_summ += element
        return self.all_initial_summ

    def get_initial_percent(self) -> list:
        all_initial_summ = self.get_all_initial_summ()
        print(f"{all_initial_summ=}")
        answer = []
        for item in self.balances:
            try:
                element: PortfolioSettings = getattr(self, item.asset)
                amount = item.free + item.locked
                if item.asset == "USDT":
                    need_summ_in_usdt = all_initial_summ * (element.need_portfolio_share / 100)
                    summ_in_usdt_more = need_summ_in_usdt * (Decimal(1) + self.max_deviation / 100)
                    summ_in_usdt_less = need_summ_in_usdt * (Decimal(1) - self.max_deviation / 100)
                    if element.summ_in_usdt > summ_in_usdt_more:
                        sell_amount = element.summ_in_usdt - need_summ_in_usdt
                        percent_of_element_now = sell_amount * 100 / element.summ_in_usdt
                        sell_amount2 = sell_amount / element.now_price
                        answer.append(
                            f"{item.asset} is more then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} > need={summ_in_usdt_more} "
                            f"{sell_amount2=} {percent_of_element_now=}"
                        )
                    elif element.summ_in_usdt < summ_in_usdt_less:
                        buy_amount = need_summ_in_usdt - element.summ_in_usdt
                        percent_of_element_now = buy_amount * 100 / element.summ_in_usdt
                        buy_amount2 = buy_amount / element.now_price
                        answer.append(
                            f"{item.asset} is less then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} < need={summ_in_usdt_less} "
                            f"{buy_amount2=} {percent_of_element_now=}"
                        )
                elif not amount == Decimal(0):
                    need_summ_in_usdt = all_initial_summ * (element.need_portfolio_share / 100)
                    summ_in_usdt_more = need_summ_in_usdt * (Decimal(1) + self.max_deviation / 100)
                    summ_in_usdt_less = need_summ_in_usdt * (Decimal(1) - self.max_deviation / 100)
                    if element.summ_in_usdt > summ_in_usdt_more:
                        sell_amount = element.summ_in_usdt - need_summ_in_usdt
                        percent_of_element_now = sell_amount * 100 / element.summ_in_usdt
                        sell_amount2 = sell_amount / element.now_price
                        answer.append(
                            f"{item.asset} is more then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} > need={summ_in_usdt_more} "
                            f"{sell_amount2=} {percent_of_element_now=}"
                        )
                    elif element.summ_in_usdt < summ_in_usdt_less:
                        buy_amount = need_summ_in_usdt - element.summ_in_usdt
                        percent_of_element_now = buy_amount * 100 / element.summ_in_usdt
                        buy_amount2 = buy_amount / element.now_price
                        answer.append(
                            f"{item.asset} is less then max_deviation {self.max_deviation}% "
                            f"now={element.summ_in_usdt} < need={summ_in_usdt_less} "
                            f"{buy_amount2=} {percent_of_element_now=}"
                        )
                else:
                    print(f"{item.asset} amount == 0")
            except AttributeError:
                print(f"We have AttributeError!!! No {item.asset} in self portfolio")
        return answer

    # def need_send_message(self) -> bool:
    #     return self.send

    # def get_message_text(self) -> str:
    #     return self.message


class MyPortfolio(Portfolio):
    def start(self) -> str:
        return "GOOD"

    # def get_all_summ(self) -> Decimal:
    #     summ = Decimal(0)
    #     for element in self.list_summ_of_portfolio:
    #         summ += element
    #     return summ


test_balance = [
    BalanceItem(
        **{
            "asset": "BTC",
            "free": 0.00245,
            "locked": 0.0,
        }
    ),
    BalanceItem(
        **{
            "asset": "NEAR",
            "free": 0.0,
            "locked": 0.0,
        }
    ),
    BalanceItem(
        **{
            "asset": "USDT",
            "free": 250.0,
            "locked": 0.0,
        }
    ),
]

test_data = [
    PortfolioSettings(
        **{
            "asset": "BTC",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "ETH",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "ATOM",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "DOT",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "SOL",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "MATIC",
            "need_portfolio_share": 5.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "GLMR",
            "need_portfolio_share": 5.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "ADA",
            "need_portfolio_share": 10.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "NEAR",
            "need_portfolio_share": 5.0,
        }
    ),
    PortfolioSettings(
        **{
            "asset": "USDT",
            "amount": 250,
            "need_portfolio_share": 25.0,
        }
    ),
]


test = MyPortfolio(portfolio_settings=test_data, max_deviation=Decimal(5.0))
print(test.start())
print(test.set_actual_portfolio_structure(test_balance))

# print(test.money_to_buy)

# print(test.get_percent())
for item in test.get_percent():
    print(f"{item}")
