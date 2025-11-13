from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, func
from .database import Base
from sqlalchemy.dialects.postgresql import CITEXT

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)  

class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    event = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)



