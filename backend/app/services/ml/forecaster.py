"""
Sales Forecasting Model — Week 2
Trains an XGBoost model on monthly revenue data and predicts next 30 days.
Usage: python -m app.services.ml.forecaster
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from app.db.database import engine

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "forecaster.pkl"


def load_training_data() -> pd.DataFrame:
    """Pull daily revenue from PostgreSQL."""
    print("  Loading training data from DB...")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                DATE_TRUNC('day', o.order_purchase_timestamp)::date AS ds,
                SUM(oi.price)                                        AS revenue,
                COUNT(DISTINCT o.order_id)                           AS order_count,
                AVG(oi.price)                                        AS avg_price
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_status = 'delivered'
              AND o.order_purchase_timestamp IS NOT NULL
            GROUP BY DATE_TRUNC('day', o.order_purchase_timestamp)::date
            ORDER BY ds
        """), conn)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar and lag features for XGBoost."""
    df = df.copy()
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.set_index("ds").asfreq("D").fillna(0).reset_index()

    # Calendar features
    df["dayofweek"]  = df["ds"].dt.dayofweek
    df["dayofmonth"] = df["ds"].dt.day
    df["month"]      = df["ds"].dt.month
    df["quarter"]    = df["ds"].dt.quarter
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    # Lag features (yesterday, last week, last month)
    df["lag_1"]  = df["revenue"].shift(1)
    df["lag_7"]  = df["revenue"].shift(7)
    df["lag_30"] = df["revenue"].shift(30)

    # Rolling averages
    df["rolling_7"]  = df["revenue"].shift(1).rolling(7).mean()
    df["rolling_30"] = df["revenue"].shift(1).rolling(30).mean()

    return df.dropna()


def train():
    """Train XGBoost forecasting model and save to disk."""
    from xgboost import XGBRegressor
    from sklearn.metrics import mean_absolute_percentage_error

    print("\n=== SmartCart Sales Forecaster — Training ===\n")

    df = load_training_data()
    df = add_time_features(df)

    FEATURES = ["dayofweek", "dayofmonth", "month", "quarter",
                "is_weekend", "lag_1", "lag_7", "lag_30",
                "rolling_7", "rolling_30"]
    TARGET = "revenue"

    # Train/test split — last 30 days as test
    split = len(df) - 30
    X_train, X_test = df[FEATURES].iloc[:split], df[FEATURES].iloc[split:]
    y_train, y_test = df[TARGET].iloc[:split], df[TARGET].iloc[split:]

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    preds = model.predict(X_test)
    mape = mean_absolute_percentage_error(y_test, preds)
    print(f"  ✓ Model trained — Test MAPE: {mape*100:.1f}%")

    # Save model + last known data for future prediction
    payload = {"model": model, "last_df": df, "features": FEATURES}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)
    print(f"  ✓ Model saved to {MODEL_PATH}")
    return mape


def predict_next_30_days() -> list[dict]:
    """Load trained model and predict next 30 days of revenue."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not trained yet. Run: python -m app.services.ml.forecaster")

    with open(MODEL_PATH, "rb") as f:
        payload = pickle.load(f)

    model   = payload["model"]
    df      = payload["last_df"].copy()
    features = payload["features"]

    last_date = df["ds"].max()
    predictions = []

    for i in range(1, 31):
        next_date = last_date + pd.Timedelta(days=i)

        # Build feature row for the next day
        row = {
            "ds":          next_date,
            "dayofweek":   next_date.dayofweek,
            "dayofmonth":  next_date.day,
            "month":       next_date.month,
            "quarter":     next_date.quarter,
            "is_weekend":  int(next_date.dayofweek >= 5),
            "lag_1":       df["revenue"].iloc[-1],
            "lag_7":       df["revenue"].iloc[-7],
            "lag_30":      df["revenue"].iloc[-30],
            "rolling_7":   df["revenue"].iloc[-7:].mean(),
            "rolling_30":  df["revenue"].iloc[-30:].mean(),
        }

        X = pd.DataFrame([row])[features]
        pred = float(model.predict(X)[0])
        pred = max(0, pred)  # no negative revenue

        predictions.append({
            "date":    next_date.strftime("%Y-%m-%d"),
            "revenue": round(pred, 2),
        })

        # Append prediction to df so next day's lags are correct
        new_row = pd.DataFrame([{"ds": next_date, "revenue": pred,
                                  "order_count": 0, "avg_price": 0,
                                  **row}])
        df = pd.concat([df, new_row], ignore_index=True)

    return predictions


if __name__ == "__main__":
    train()
    print("\nSample 7-day forecast:")
    preds = predict_next_30_days()
    for p in preds[:7]:
        print(f"  {p['date']}: R$ {p['revenue']:,.2f}")