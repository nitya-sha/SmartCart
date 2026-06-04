from pydantic import BaseModel
from typing import Optional


class OrderSummary(BaseModel):
    total_orders: int
    total_revenue: float
    avg_order_value: float
    avg_review_score: float
    total_customers: int
    total_sellers: int


class CategoryRevenue(BaseModel):
    category: str
    order_count: int
    revenue: float
    avg_review_score: float


class MonthlyTrend(BaseModel):
    month: str
    orders: int
    revenue: float


class TopProduct(BaseModel):
    product_id: str
    category: str
    times_ordered: int
    total_revenue: float
    avg_review_score: float


class CustomerProfile(BaseModel):
    customer_unique_id: str
    city: Optional[str]
    state: Optional[str]
    total_orders: int
    total_spend: float
    avg_review_score: float
    favourite_category: Optional[str]
    first_order: Optional[str]
    last_order: Optional[str]


class DeliveryPerformance(BaseModel):
    avg_delivery_days: float
    late_delivery_pct: float
    delivered_count: int


class HealthCheck(BaseModel):
    status: str
    db_connected: bool
    version: str = "1.0.0"