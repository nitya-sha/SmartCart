"""
Analytics service — all the business logic for dashboard queries.
Each function returns clean Python dicts/lists, no SQLAlchemy objects,
so FastAPI can serialize them directly.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional


def get_order_summary(db: Session) -> dict:
    """High-level KPIs: total orders, revenue, avg order value, avg review score."""
    result = db.execute(text("""
        SELECT
            COUNT(DISTINCT o.order_id)                          AS total_orders,
            ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue,
            ROUND(AVG(oi.price + oi.freight_value)::numeric, 2) AS avg_order_value,
            ROUND(AVG(r.review_score)::numeric, 2)              AS avg_review_score,
            COUNT(DISTINCT o.customer_id)                       AS total_customers,
            COUNT(DISTINCT oi.seller_id)                        AS total_sellers
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
    """)).fetchone()

    return {
        "total_orders": result.total_orders,
        "total_revenue": float(result.total_revenue or 0),
        "avg_order_value": float(result.avg_order_value or 0),
        "avg_review_score": float(result.avg_review_score or 0),
        "total_customers": result.total_customers,
        "total_sellers": result.total_sellers,
    }


def get_revenue_by_category(db: Session, limit: int = 15) -> list[dict]:
    """Revenue, order count, and avg review score per product category."""
    rows = db.execute(text("""
        SELECT
            COALESCE(p.product_category_name, 'unknown')        AS category,
            COUNT(DISTINCT o.order_id)                          AS order_count,
            ROUND(SUM(oi.price)::numeric, 2)                    AS revenue,
            ROUND(AVG(r.review_score)::numeric, 2)              AS avg_review_score
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        LEFT JOIN order_reviews r ON r.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY p.product_category_name
        ORDER BY revenue DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        {
            "category": row.category,
            "order_count": row.order_count,
            "revenue": float(row.revenue),
            "avg_review_score": float(row.avg_review_score or 0),
        }
        for row in rows
    ]


def get_monthly_revenue_trend(db: Session) -> list[dict]:
    """Month-over-month revenue trend for the full dataset."""
    rows = db.execute(text("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', o.order_purchase_timestamp), 'YYYY-MM') AS month,
            COUNT(DISTINCT o.order_id)                                           AS orders,
            ROUND(SUM(oi.price)::numeric, 2)                                     AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp IS NOT NULL
        GROUP BY DATE_TRUNC('month', o.order_purchase_timestamp)
        ORDER BY DATE_TRUNC('month', o.order_purchase_timestamp)
    """)).fetchall()

    return [
        {"month": row.month, "orders": row.orders, "revenue": float(row.revenue)}
        for row in rows
    ]


def get_top_products(db: Session, limit: int = 20) -> list[dict]:
    """Top products by revenue with their review scores."""
    rows = db.execute(text("""
        SELECT
            oi.product_id,
            p.product_category_name                             AS category,
            COUNT(*)                                            AS times_ordered,
            ROUND(SUM(oi.price)::numeric, 2)                   AS total_revenue,
            ROUND(AVG(r.review_score)::numeric, 2)             AS avg_review_score
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        LEFT JOIN order_reviews r ON r.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY oi.product_id, p.product_category_name
        ORDER BY total_revenue DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        {
            "product_id": row.product_id,
            "category": row.category or "unknown",
            "times_ordered": row.times_ordered,
            "total_revenue": float(row.total_revenue),
            "avg_review_score": float(row.avg_review_score or 0),
        }
        for row in rows
    ]


def get_customer_profile(db: Session, customer_unique_id: str) -> Optional[dict]:
    """Full profile for one customer: orders, spend, favourite category."""
    result = db.execute(text("""
        SELECT
            c.customer_unique_id,
            c.customer_city,
            c.customer_state,
            COUNT(DISTINCT o.order_id)                          AS total_orders,
            ROUND(SUM(oi.price)::numeric, 2)                   AS total_spend,
            ROUND(AVG(r.review_score)::numeric, 2)             AS avg_review_score,
            MODE() WITHIN GROUP (ORDER BY p.product_category_name) AS favourite_category,
            MIN(o.order_purchase_timestamp)                     AS first_order,
            MAX(o.order_purchase_timestamp)                     AS last_order
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        LEFT JOIN order_reviews r ON r.order_id = o.order_id
        WHERE c.customer_unique_id = :uid
          AND o.order_status = 'delivered'
        GROUP BY c.customer_unique_id, c.customer_city, c.customer_state
    """), {"uid": customer_unique_id}).fetchone()

    if not result:
        return None

    return {
        "customer_unique_id": result.customer_unique_id,
        "city": result.customer_city,
        "state": result.customer_state,
        "total_orders": result.total_orders,
        "total_spend": float(result.total_spend or 0),
        "avg_review_score": float(result.avg_review_score or 0),
        "favourite_category": result.favourite_category,
        "first_order": str(result.first_order)[:10] if result.first_order else None,
        "last_order": str(result.last_order)[:10] if result.last_order else None,
    }


def get_delivery_performance(db: Session) -> dict:
    """Average delivery time and late delivery rate."""
    result = db.execute(text("""
        SELECT
            ROUND(AVG(
                EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp))
                / 86400
            )::numeric, 1)                                      AS avg_delivery_days,
            ROUND(100.0 * COUNT(*) FILTER (
                WHERE order_delivered_customer_date > order_estimated_delivery_date
            ) / NULLIF(COUNT(*), 0), 1)                         AS late_delivery_pct,
            COUNT(*) FILTER (
                WHERE order_status = 'delivered'
            )                                                    AS delivered_count
        FROM orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    """)).fetchone()

    return {
        "avg_delivery_days": float(result.avg_delivery_days or 0),
        "late_delivery_pct": float(result.late_delivery_pct or 0),
        "delivered_count": result.delivered_count,
    }