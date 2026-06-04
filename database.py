import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base

# Берем ссылку на БД из сервера, либо используем локальную
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ege_math.db")

# Фикс для облачных баз (иногда они выдают postgres:// вместо postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _ensure_columns():
    """Безопасно добавляет недостающие столбцы в уже существующие таблицы.
    Работает и для SQLite, и для PostgreSQL (ALTER TABLE ADD COLUMN)."""
    wanted = {
        "questions": [("solution", "VARCHAR")],
        "spaced_repetition": [("repetitions", "INTEGER DEFAULT 0")],
    }
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, cols in wanted.items():
            if table not in existing_tables:
                continue
            have = {c["name"] for c in insp.get_columns(table)}
            for name, coltype in cols:
                if name not in have:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {coltype}'))


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_columns()