"""
Product Recommendation Engine — Week 2
Uses collaborative filtering (item-item cosine similarity) on purchase history.
Usage: python -m app.services.ml.recommender
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from app.db.database import engine

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "recommender.pkl"


def load_purchase_data() -> pd.DataFrame:
    """Load customer → product purchase matrix from DB."""
    print("  Loading purchase data from DB...")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                c.customer_unique_id,
                oi.product_id,
                COUNT(*)        AS purchase_count,
                SUM(oi.price)   AS total_spend
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id, oi.product_id
        """), conn)
    return df


def load_product_metadata() -> pd.DataFrame:
    """Load product category info for display."""
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                p.product_id,
                p.product_category_name                         AS category,
                ROUND(AVG(oi.price)::numeric, 2)               AS avg_price,
                COUNT(oi.order_id)                              AS times_ordered,
                ROUND(AVG(r.review_score)::numeric, 2)         AS avg_review_score
            FROM products p
            JOIN order_items oi ON oi.product_id = p.product_id
            JOIN orders o ON o.order_id = oi.order_id
            LEFT JOIN order_reviews r ON r.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY p.product_id, p.product_category_name
        """), conn)
    return df


def train():
    """Build item-item similarity matrix and save to disk."""
    from sklearn.metrics.pairwise import cosine_similarity

    print("\n=== SmartCart Recommender — Training ===\n")

    purchases = load_purchase_data()
    metadata  = load_product_metadata()

    # Keep only products with 10+ purchases (reduces noise)
    popular = purchases.groupby("product_id")["purchase_count"].sum()
    popular = popular[popular >= 10].index
    purchases = purchases[purchases["product_id"].isin(popular)]

    print(f"  Building matrix: {purchases['customer_unique_id'].nunique():,} customers "
          f"× {purchases['product_id'].nunique():,} products")

    # Build customer-product matrix (binary: bought or not)
    matrix = purchases.pivot_table(
        index="customer_unique_id",
        columns="product_id",
        values="purchase_count",
        fill_value=0,
    )
    matrix = (matrix > 0).astype(float)  # binary

    # Item-item cosine similarity
    item_sim = cosine_similarity(matrix.T)
    item_sim_df = pd.DataFrame(item_sim, index=matrix.columns, columns=matrix.columns)

    payload = {
        "similarity": item_sim_df,
        "matrix":     matrix,
        "metadata":   metadata.set_index("product_id"),
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)

    print(f"  ✓ Similarity matrix built: {item_sim_df.shape}")
    print(f"  ✓ Recommender saved to {MODEL_PATH}")


def get_recommendations(customer_unique_id: str, top_n: int = 5) -> list[dict]:
    """
    Return top_n product recommendations for a customer.
    Strategy: find products similar to what they've bought, that they haven't bought yet.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Recommender not trained yet. Run: python -m app.services.ml.recommender")

    with open(MODEL_PATH, "rb") as f:
        payload = pickle.load(f)

    sim      = payload["similarity"]
    matrix   = payload["matrix"]
    metadata = payload["metadata"]

    # If customer not in matrix, return top popular products
    if customer_unique_id not in matrix.index:
        return get_popular_products(metadata, top_n)

    # Products this customer has bought
    bought = matrix.loc[customer_unique_id]
    bought_products = bought[bought > 0].index.tolist()

    if not bought_products:
        return get_popular_products(metadata, top_n)

    # Score = sum of similarity to all bought products
    scores = sim[bought_products].sum(axis=1)

    # Remove already-bought products
    scores = scores.drop(index=[p for p in bought_products if p in scores.index], errors="ignore")
    scores = scores.sort_values(ascending=False)

    recommendations = []
    for product_id in scores.head(top_n).index:
        if product_id in metadata.index:
            row = metadata.loc[product_id]
            recommendations.append({
                "product_id":       product_id,
                "category":         str(row.get("category", "unknown")),
                "avg_price":        float(row.get("avg_price", 0)),
                "times_ordered":    int(row.get("times_ordered", 0)),
                "avg_review_score": float(row.get("avg_review_score", 0)),
                "similarity_score": round(float(scores[product_id]), 4),
            })

    return recommendations


def get_popular_products(metadata: pd.DataFrame, top_n: int) -> list[dict]:
    """Fallback: return most ordered products for new customers."""
    top = metadata.nlargest(top_n, "times_ordered")
    return [
        {
            "product_id":       pid,
            "category":         str(row.get("category", "unknown")),
            "avg_price":        float(row.get("avg_price", 0)),
            "times_ordered":    int(row.get("times_ordered", 0)),
            "avg_review_score": float(row.get("avg_review_score", 0)),
            "similarity_score": 0.0,
        }
        for pid, row in top.iterrows()
    ]


if __name__ == "__main__":
    train()
    print("\nSample recommendations for a random customer:")
    import pickle
    with open(MODEL_PATH, "rb") as f:
        p = pickle.load(f)
    sample_customer = p["matrix"].index[0]
    print(f"Customer: {sample_customer}")
    recs = get_recommendations(sample_customer)
    for r in recs:
        print(f"  {r['category']:30s} | R$ {r['avg_price']:7.2f} | ⭐ {r['avg_review_score']}")