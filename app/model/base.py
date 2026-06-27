from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(
            db_url,
            echo=False,
            future=True,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )

    def init_db(self):
        Base.metadata.create_all(self.engine)
        self.migrate_db()

    def migrate_db(self):
        inspector = inspect(self.engine)
        columns = {column["name"] for column in inspector.get_columns("subscription_sources")}
        if "last_successful_fetch_at" not in columns:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE subscription_sources ADD COLUMN last_successful_fetch_at DATETIME"))

    @contextmanager
    def session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
