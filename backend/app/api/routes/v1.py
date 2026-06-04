from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, check_db_connection
from app.services import analytics
from app.schemas.responses import (
    OrderSummary,
    CategoryRevenue,
    MonthlyTrend,
    TopProduct,
    CustomerProfile,
    DeliveryPerformance,
    HealthCheck,
)

router = APIRouter()


# ── Health ──────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthCheck, tags=["System"])
def health_check():
    """Check if the API and database are up."""
    return HealthCheck(
        status="ok",
        db_connected=check_db_connection(),
    )


# ── Orders ───────────────────────────────────────────────────────────────────

@router.get("/orders/summary", response_model=OrderSummary, tags=["Orders"])
def order_summary(db: Session = Depends(get_db)):
    """Return high-level KPIs: total orders, revenue, AOV, review score."""
    return analytics.get_order_summary(db)


@router.get("/orders/revenue-by-category", response_model=list[CategoryRevenue], tags=["Orders"])
def revenue_by_category(limit: int = 15, db: Session = Depends(get_db)):
    """Revenue breakdown by product category, sorted descending."""
    return analytics.get_revenue_by_category(db, limit=limit)


@router.get("/orders/monthly-trend", response_model=list[MonthlyTrend], tags=["Orders"])
def monthly_trend(db: Session = Depends(get_db)):
    """Month-over-month revenue and order volume trend."""
    return analytics.get_monthly_revenue_trend(db)


@router.get("/orders/delivery-performance", response_model=DeliveryPerformance, tags=["Orders"])
def delivery_performance(db: Session = Depends(get_db)):
    """Avg delivery time and late delivery rate."""
    return analytics.get_delivery_performance(db)


# ── Products ─────────────────────────────────────────────────────────────────

@router.get("/products/top", response_model=list[TopProduct], tags=["Products"])
def top_products(limit: int = 20, db: Session = Depends(get_db)):
    """Top products by total revenue."""
    return analytics.get_top_products(db, limit=limit)


# ── Customers ─────────────────────────────────────────────────────────────────

@router.get("/customers/{customer_unique_id}", response_model=CustomerProfile, tags=["Customers"])
def customer_profile(customer_unique_id: str, db: Session = Depends(get_db)):
    """Full profile for a single customer by their unique ID."""
    profile = analytics.get_customer_profile(db, customer_unique_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found")
    return profile