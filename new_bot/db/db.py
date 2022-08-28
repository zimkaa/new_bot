from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session

from settings import DB_NAME


Base = declarative_base()


def create_db():
    engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
    Base.metadata.create_all(engine)


def connect_db():
    # engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
    # session = sessionmaker(bind=engine)
    engine = create_engine(f"sqlite:///{DB_NAME}")
    session = Session(bind=engine.connect())
    return session
