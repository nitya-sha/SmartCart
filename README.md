# SmartCart 🛒
**AI-powered E-Commerce Analytics & Recommendation Engine**

A full-stack web app that ingests real sales data, detects trends with ML, and serves personalised product recommendations.

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.12, FastAPI |
| Database | PostgreSQL (Railway for cloud) |
| ML | scikit-learn, XGBoost, pandas |
| Frontend | React 18, Recharts |
| Deployment | Render (backend), Vercel (frontend) |

---

## Project Structure
```
smartcart/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── core/            # Config, settings
│   │   ├── db/              # Database connection, session
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── tests/               # Pytest test files
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   └── src/                 # React app (Week 3)
├── notebooks/
│   └── week1_eda.ipynb      # Exploratory data analysis
├── data/
│   └── raw/                 # Raw Olist CSV files (gitignored)
└── README.md
```

---

## Week 1 Setup

### 1. Get the Dataset
Download from Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Place all CSVs into `data/raw/`

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 4. Setup Database
```bash
# Create DB and load data
python -m app.db.init_db
python -m app.services.data_loader
```

### 5. Run the API
```bash
uvicorn main:app --reload
# API docs at: http://localhost:8000/docs
```

---

## API Endpoints (Week 1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/orders/summary` | Order stats overview |
| GET | `/api/v1/orders/revenue-by-category` | Revenue per category |
| GET | `/api/v1/orders/monthly-trend` | Monthly revenue trend |
| GET | `/api/v1/customers/{id}` | Customer profile |
| GET | `/api/v1/products/top` | Top selling products |

---

## Dataset: Olist Brazilian E-Commerce
100k+ real orders from 2016–2018. Key tables used:
- `olist_orders_dataset.csv` — order status, timestamps
- `olist_order_items_dataset.csv` — products per order, price
- `olist_customers_dataset.csv` — customer location
- `olist_products_dataset.csv` — product categories
- `olist_order_reviews_dataset.csv` — review scores
- `olist_sellers_dataset.csv` — seller info

---

## Author
IIT Madras BS Data Science & Applications