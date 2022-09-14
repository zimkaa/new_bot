# # # offset = -2
# # # new_offset = offset - 1

# # # # list_klines = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

# # # list_klines = range(60)

# # # new = 10

# # # for kline in list_klines[new_offset:new:-1]:
# # #     print(kline)


# # # ddd = {"out": 2, "income": 4}

# # # for key, value in ddd.items():
# # #     print(f"{key=} {value=}")
# # #     print(f"{ddd.get(key)}")


# # # class Testor:
# # #     def __init__(self, ddd: dict):
# # #         for key, value in ddd.items():
# # #             eval(f"self.{key}")
# # #             print(f"{ddd.get(key)}")


# # # ggg = Testor(ddd)

# # # print(ggg.income)

# # ##################################################################################
# # ##################################################################################
# # ##################################################################################

# # # from pydantic import BaseModel, Field
# # # from enum import Enum


# # # # class BugStatus(enum.Enum):

# # # #     new = 7
# # # #     incomplete = 6
# # # #     invalid = 5
# # # #     wont_fix = 4
# # # #     in_progress = 3
# # # #     fix_committed = 2
# # # #     fix_released = 1

# # # #     by_design = 4
# # # #     closed = 1


# # # # for status in BugStatus:
# # # #     print("{:15} = {}".format(status.name, status.value))


# # # # print("\nSame: by_design is wont_fix: ", BugStatus.by_design is BugStatus.wont_fix)
# # # # print("Same: closed is fix_released: ", BugStatus.closed is BugStatus.fix_released)


# # # class Asset(BaseModel):
# # #     asset: str


# # # class BalanceItem(Asset):
# # #     free: float
# # #     locked: float


# # # class Account(BaseModel):
# # #     maker_commission: int = Field(alias="makerCommission")
# # #     taker_commission: int = Field(alias="takerCommission")
# # #     buyer_commission: int = Field(alias="buyerCommission")
# # #     seller_commission: int = Field(alias="sellerCommission")
# # #     can_trade: bool = Field(alias="canTrade")
# # #     can_withdraw: bool = Field(alias="canWithdraw")
# # #     can_deposit: bool = Field(alias="canDeposit")
# # #     update_time: int = Field(alias="updateTime")
# # #     account_type: str = Field(alias="accountType")
# # #     balances: list[BalanceItem]
# # #     permissions: list[str]


# # # class PortfolioSettings(Asset):
# # #     amount: float = 0.0
# # #     now_price: float = 0.0
# # #     purchase_price: float = 0.0
# # #     now_portfolio_share: float = 0.0
# # #     need_portfolio_share: float = 0.0


# # # class Tiker(Enum):
# # #     BTC = "BTC"
# # #     NEAR = "NEAR"
# # #     ETH = "ETH"
# # #     ADA = "ADA"


# # # def create_tiker_dict() -> dict[Tiker, PortfolioSettings]:
# # #     tiker_dict: dict = dict()
# # #     for tiker in Tiker:
# # #         tiker_dict[tiker.value] = PortfolioSettings(asset=tiker.value)
# # #     return tiker_dict


# # # print(create_tiker_dict())

# # ##################################################################################
# # ##################################################################################
# # ##################################################################################


# # # class Ut:
# # #     def __init__(self, iterable):
# # #         print(f"inti {iterable}")
# # #         for k in iterable:
# # #             setattr(self, k, k)

# # #     # def get_myitter(self):
# # #     #     string = ""
# # #     #     for it in self:
# # #     #         string += it
# # #     #     return f"{string}"

# # #     # def __setitem__(self, key, value):
# # #     #     setattr(self, key, value)

# # #     # def __new__(cls, iterable):
# # #     #     print(f"inti {iterable}")
# # #     #     for i, arg in enumerate(iterable):
# # #     #         self[i] = arg.upper()
# # #     #     new_iterable =
# # #     #     return super().__new__(cls, new_iterable)


# # # new_cls = Ut(["hi", "hellow"])

# # # print(new_cls)
# # # print(dir(new_cls))
# # # print(new_cls.hi)

# # # # print(f"{new_cls[0]}")


# # ##################################################################################
# # ##################################################################################
# # ##################################################################################


# # # class DictAttr:
# # #     def __init__(self, args):
# # #         if isinstance(args, list):
# # #             args = dict(args)

# # #         for k in args:
# # #             setattr(self, k, args[k])
# # #             setattr(self, "get_" + k, lambda k=k: getattr(self, k))

# # #     def __getitem__(self, item):
# # #         return getattr(self, item)

# # #     def __setitem__(self, key, value):
# # #         setattr(self, key, value)

# # #     def __repr__(self) -> str:
# # #         return f"{self.iterable}"


# # # x = DictAttr({"k": 5, "l": "ss", "g": 4})

# # # print(x.get_g())
# # # # print(x.)

# # # # print(dir(x))

# # # a, b = [[1], 2]
# # # print(a)
# # # a[:] = 2, 3, 4

# # # print(a)


# # # print(121 // 60)


# # def my_f():
# #     try:
# #         return 10
# #     finally:
# #         return 20


# # res = my_f()
# # print(res)


# from logic import get_klines_for_period


# coin_name = "BTC"

# list_klines = get_klines_for_period(coin_name, limit=60)

# # print(f"{list_klines=}")

# offset = -2
# new_offset = offset - 1
# # all_change = change_persent
# for kline in list_klines[new_offset::-1]:
#     print(f"{kline.time_open=}")
