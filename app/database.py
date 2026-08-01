from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

print("DATABASE_URL =", DATABASE_URL)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)
print("DATABASE_URL =", DATABASE_URL)

if DATABASE_URL.startswith("sqlite:///"):
    import os
    ruta = DATABASE_URL.replace("sqlite:///", "")
    print("Base SQLite absoluta:", os.path.abspath(ruta))
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        