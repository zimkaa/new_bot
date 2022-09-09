from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base

from settings import DB_NAME


Base = declarative_base()


def create_db():
    engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
    Base.metadata.create_all(engine)


def connect_db():
    engine = create_engine(f"sqlite:///{DB_NAME}")
    session = Session(bind=engine.connect())
    return session


def write_error_log_to_db():
    engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
    Base.metadata.create_all(engine)
