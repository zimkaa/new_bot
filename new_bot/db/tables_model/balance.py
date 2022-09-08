import datetime
from decimal import Decimal

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import DECIMAL
from sqlalchemy import Integer
from sqlalchemy import String

from db import Base


class Balance(Base):
    __tablename__ = "Balance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_name = Column(String, nullable=False)
    balance = Column(DECIMAL, nullable=False)
    profit = Column(DECIMAL, nullable=False)
    time = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, *, coin_name: str, balance: Decimal, profit: Decimal):
        self.coin_name = coin_name
        self.balance = balance
        self.profit = profit

    def __repr__(self) -> str:
        return f"Users(error={self.coin_name!r}, " f"balance={self.balance!r}, " f"profit={self.profit!r}, "
