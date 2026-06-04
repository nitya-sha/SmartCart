"""
ML API endpoints — Week 2
Adds forecasting and recommendation endpoints to SmartCart API.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class DailyForecast(BaseModel):
    date: str
    revenue: float


class Recommendation(BaseModel):
    product_id: str
    category: str
    avg_price: float
    times_ordered: int
    avg_review_score: float
    similarity_score: float


class TrainResponse(BaseModel):
    status: str
    message: str
    mape_pct: float | None = None


# ── Forecasting ───────────────────────────────────────────────────────────────

@router.post("/ml/train/forecaster", response_model=TrainResponse, tags=["ML"])
def train_forecaster():
    """Train the XGBoost sales forecasting model. Takes ~30 seconds."""
    try:
        from app.services.ml.forecaster import train
        mape = train()
        return TrainResponse(
            status="ok",
            message="Forecasting model trained successfully",
            mape_pct=round(mape * 100, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/forecast", response_model=list[DailyForecast], tags=["ML"])
def get_forecast(days: int = Query(default=30, ge=1, le=90)):
    """Get revenue forecast for the next N days (default 30)."""
    try:
        from app.services.ml.forecaster import predict_next_30_days
        predictions = predict_next_30_days()
        return predictions[:days]
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained yet. Call POST /api/v1/ml/train/forecaster first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Recommendations ───────────────────────────────────────────────────────────

@router.post("/ml/train/recommender", response_model=TrainResponse, tags=["ML"])
def train_recommender():
    """Train the collaborative filtering recommender. Takes ~60 seconds."""
    try:
        from app.services.ml.recommender import train
        train()
        return TrainResponse(
            status="ok",
            message="Recommender model trained successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/recommend/{customer_unique_id}", response_model=list[Recommendation], tags=["ML"])
def get_recommendations(customer_unique_id: str, top_n: int = Query(default=5, ge=1, le=20)):
    """Get product recommendations for a customer by their unique ID."""
    try:
        from app.services.ml.recommender import get_recommendations
        return get_recommendations(customer_unique_id, top_n=top_n)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained yet. Call POST /api/v1/ml/train/recommender first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/recommend/popular", response_model=list[Recommendation], tags=["ML"])
def get_popular(top_n: int = Query(default=10, ge=1, le=50)):
    """Get most popular products (fallback for new customers)."""
    try:
        from app.services.ml.recommender import get_popular_products, MODEL_PATH
        import pickle
        with open(MODEL_PATH, "rb") as f:
            payload = pickle.load(f)
        return get_popular_products(payload["metadata"], top_n)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained yet. Call POST /api/v1/ml/train/recommender first."
        )