from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, JSON
from models.base import Base  # import from your shared base

class BuxferTransaction(Base):
    __tablename__ = 'buxfer_transactions'

    id = Column(Integer, primary_key=True, autoincrement=False, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=True)
    transactionType = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    expenseAmount = Column(Float, nullable=True)
    accountId = Column(Integer, ForeignKey('buxfer_accounts.id'), nullable=True)
    accountName = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    tagNames = Column(JSON, nullable=True)
    status = Column(String, nullable=True)
    isFutureDated = Column(Boolean, nullable=False)
    isPending = Column(Boolean, nullable=False)
    userName = Column(String, nullable=False)
    fromAccount = Column(JSON, nullable=True) 
    toAccount = Column(JSON, nullable=True) 
