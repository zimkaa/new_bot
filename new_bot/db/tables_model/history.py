import datetime
from decimal import Decimal

from sqlalchemy import Column
from sqlalchemy import DECIMAL
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from db import Base


class History(Base):
    __tablename__ = "historys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_name = Column(String, nullable=False)
    amount = Column(DECIMAL, nullable=False)
    operation_type = Column(String, nullable=False)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(DECIMAL, nullable=False)

    def __init__(self, *, coin_name: str, amount: Decimal, operation_type: str, price: Decimal):
        self.coin_name = coin_name
        self.amount = amount
        self.operation_type = operation_type
        self.price = price

    def __repr__(self) -> str:
        return (
            f"Users(coin_name={self.coin_name!r}, operation_type={self.operation_type}, "
            f"amount={self.amount!r}, "
            f"time={self.time!r}, price={self.price}"
        )
