from datetime import datetime
from secrets import token_urlsafe

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.model.base import Base


def generate_subscription_key():
    return token_urlsafe(32)


class SubscriptionSource(Base):
    __tablename__ = "subscription_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=generate_subscription_key,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.datetime("now"),
        onupdate=func.datetime("now"),
    )
    last_successful_fetch_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_fetch_status: Mapped[str | None] = mapped_column(String, nullable=True)
