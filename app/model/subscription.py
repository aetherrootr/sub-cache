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


class SubscriptionSource(Base):
    __tablename__ = "subscription_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.datetime("now"),
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.datetime("now"),
        onupdate=func.datetime("now"),
    )
