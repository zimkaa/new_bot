import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import DECIMAL
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from db import Base


class Coin(Base):
    __tablename__ = "coin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_name = Column(String, nullable=False, unique=True)
    amount = Column(DECIMAL, nullable=False)
    balance = Column(Integer, nullable=False)
    buy_time = Column(DateTime, default=datetime.datetime.utcnow)
    buy_price = Column(DECIMAL, ForeignKey("roles.id"), nullable=False)
    current_price = Column(DECIMAL, nullable=False)
    sell_price = Column(DateTime, default=datetime.datetime.utcnow)
    sell_price = Column(DECIMAL, ForeignKey("roles.id"), nullable=False)
    roles = Column(String, nullable=False)
    create_at = Column(DateTime, default=datetime.datetime.utcnow)
    delete_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, *, user_name: str, full_name: str, email: str, hash_password: str, roles: str):
        self.user_name = user_name
        self.full_name = full_name
        self.email = email
        self.hash_password = hash_password
        self.roles = roles

    def __repr__(self) -> str:
        return (
            f"Users(user_name={self.user_name!r}, email={self.email}, "
            f"full_name={self.full_name!r}, "
            f"hash_password={self.hash_password!r}, roles={self.roles}"
        )
