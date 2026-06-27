from contextlib import contextmanager
from secrets import token_urlsafe

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
        if "last_fetch_status" not in columns:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE subscription_sources ADD COLUMN last_fetch_status VARCHAR"))
        if "subscription_key" not in columns:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE subscription_sources ADD COLUMN subscription_key VARCHAR"))

        with self.engine.begin() as conn:
            existing_keys = {
                row[0]
                for row in conn.execute(
                    text("SELECT subscription_key FROM subscription_sources WHERE subscription_key IS NOT NULL"),
                )
            }
            rows_without_keys = list(conn.execute(
                text("SELECT id FROM subscription_sources WHERE subscription_key IS NULL"),
            ))
            for row in rows_without_keys:
                subscription_key = token_urlsafe(32)
                while subscription_key in existing_keys:
                    subscription_key = token_urlsafe(32)
                existing_keys.add(subscription_key)
                conn.execute(
                    text("UPDATE subscription_sources SET subscription_key = :key WHERE id = :id"),
                    {"key": subscription_key, "id": row[0]},
                )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "ix_subscription_sources_subscription_key "
                    "ON subscription_sources(subscription_key)",
                ),
            )

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
