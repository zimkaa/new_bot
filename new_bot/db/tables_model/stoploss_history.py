import datetime

# from decimal import Decimal

from sqlalchemy import Column
from sqlalchemy import DECIMAL
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from db import Base


class STHistory(Base):
    __tablename__ = "stop loss history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_name = Column(String, nullable=False)
    stop_loss_price = Column(DECIMAL, nullable=False)
    time = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, *, coin_name: str, stop_loss_price: float):
        self.coin_name = coin_name
        self.stop_loss_price = stop_loss_price

    def __repr__(self) -> str:
        return f"Users(coin_name={self.coin_name!r}, stop_loss_price={self.stop_loss_price}, " f"time={self.time!r}"
