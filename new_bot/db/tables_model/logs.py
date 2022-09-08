import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import DECIMAL
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from db import Base


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    error = Column(String, nullable=False)
    error_type = Column(String, nullable=False)
    create_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, *, error: str, error_type: str):
        self.error = error
        self.error_type = error_type

    def __repr__(self) -> str:
        return (
            f"Users(error={self.error!r}, "
            f"error_type={self.error_type!r}, "
        )
