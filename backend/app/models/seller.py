from sqlalchemy import Column, String
from app.db.database import Base


class Seller(Base):
    __tablename__ = "sellers"

    seller_id = Column(String(64), primary_key=True, index=True)
    seller_zip_code_prefix = Column(String(10))
    seller_city = Column(String(64))
    seller_state = Column(String(4))