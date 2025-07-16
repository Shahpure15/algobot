from sqlalchemy import Column, Integer, Numeric, DateTime, String, func
from app.core.database import database, Base

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    side = Column(String(4), nullable=False)
    quantity = Column(Numeric(16, 8), nullable=False)
    price = Column(Numeric(16, 8), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())