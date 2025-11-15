from sqlalchemy import Column, Integer, String, Float, Date
from models.base import Base  # import from your shared base

class BuxferAccount(Base):
    __tablename__ = 'buxfer_accounts'

    id = Column(Integer, primary_key=True, autoincrement=False, nullable=False)
    name = Column(String, nullable=False)
    bank = Column(String, nullable=True)
    balance = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    lastSynced = Column(Date, nullable=True)
    availableCredit = Column(Float, nullable=True)
    totalCreditLine = Column(Float, nullable=True)
    userName = Column(String, nullable=False)
    interestRate = Column(Float, nullable=True) 
    apr = Column(Float, nullable=True) 
