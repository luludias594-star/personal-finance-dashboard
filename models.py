from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    
    transactions = relationship("Transaction", back_populates="owner")
    budgets = relationship("Budget", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    date = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="budgets")