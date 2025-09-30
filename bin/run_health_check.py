from app.db import SessionLocal
from app.jobs.health_check import run_health_check

if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_health_check(db)
    finally:
        db.close()
