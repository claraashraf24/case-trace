from sqlalchemy import text

from app.db.session import SessionLocal


def check_database_connection() -> bool:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False