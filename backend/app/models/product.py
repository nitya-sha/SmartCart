from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(64), primary_key=True, index=True)
    product_category_name = Column(String(128), index=True)
    product_name_length = Column(Integer)
    product_description_length = Column(Integer)
    product_photos_qty = Column(Integer)
    product_weight_g = Column(Float)
    product_length_cm = Column(Float)
    product_height_cm = Column(Float)
    product_width_cm = Column(Float)

    order_items = relationship("OrderItem", back_populates="product")