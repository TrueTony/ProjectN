from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy import Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class TransactionStatus(str, Enum):
    QUEUED = 'queued'
    COMPLETED = 'completed'
    REJECTED = 'rejected'


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Float)
    status = Column(Enum("queued", "completed", "rejected", name="TransactionStatus"), default="queued")
    created_at = Column(DateTime, default=func.now())

    client = relationship("Client", back_populates="transactions")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    balance = Column(Float, default=0)

    transactions = relationship("Transaction", back_populates="client")
