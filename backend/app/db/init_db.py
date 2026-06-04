"""
Run this once to create all tables in your PostgreSQL database.
Usage: python -m app.db.init_db
"""
from app.db.database import engine, Base

# Import all models so Base knows about them
from app.models import order, customer, product, seller  # noqa: F401


def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done! All tables created.")


if __name__ == "__main__":
    init_db()