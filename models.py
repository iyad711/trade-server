from sqlalchemy import Column, Integer, String, Float
from database import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ticket = Column(String, unique=True)
    symbol = Column(String)
    type = Column(String)
    lot = Column(Float)
    entry = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    status = Column(String)
