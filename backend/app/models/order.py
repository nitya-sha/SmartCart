from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), index=True)
    order_status = Column(String(32), nullable=False)
    order_purchase_timestamp = Column(DateTime)
    order_approved_at = Column(DateTime)
    order_delivered_carrier_date = Column(DateTime)
    order_delivered_customer_date = Column(DateTime)
    order_estimated_delivery_date = Column(DateTime)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    reviews = relationship("OrderReview", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id = Column(String(64), ForeignKey("orders.order_id"), primary_key=True)
    order_item_id = Column(Integer, primary_key=True)
    product_id = Column(String(64), ForeignKey("products.product_id"), index=True)
    seller_id = Column(String(64), ForeignKey("sellers.seller_id"))
    shipping_limit_date = Column(DateTime)
    price = Column(Float, nullable=False)
    freight_value = Column(Float)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class OrderReview(Base):
    __tablename__ = "order_reviews"

    review_id = Column(String(64), primary_key=True)
    order_id = Column(String(64), ForeignKey("orders.order_id"), index=True)
    review_score = Column(Integer)
    review_comment_title = Column(Text)
    review_comment_message = Column(Text)
    review_creation_date = Column(DateTime)
    review_answer_timestamp = Column(DateTime)

    order = relationship("Order", back_populates="reviews")