from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    customer_unique_id = Column(String(64), index=True)
    customer_zip_code_prefix = Column(String(10))
    customer_city = Column(String(64))
    customer_state = Column(String(4))

    orders = relationship("Order", back_populates="customer")