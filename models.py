from sqlalchemy import Column, Integer, String, BigInteger, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from db import Base, engine

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    name = Column(String)
    lang = Column(String(3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric, nullable=False)
    type = Column(String, nullable=False)  # 'income' или 'expense'
    category = Column(String)
    description = Column(Text)
    date_created = Column(DateTime(timezone=True), server_default=func.now())

# Создание таблиц
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
