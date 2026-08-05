"""Portal data model.

Phase 11a ships only the ``User`` model. Roles / features / permissions
(modular RBAC) arrive in Phase 11b.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # Identity provider: "github", "google", or "stub".
    provider: Mapped[str] = mapped_column(String(32))
    # Provider's stable subject/user id (empty for the stub user).
    provider_sub: Mapped[str] = mapped_column(String(255), default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    avatar: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def public_dict(self) -> dict[str, object]:
        """Serializable, non-sensitive view returned by /me."""
        return {
            "id": self.id,
            "email": self.email,
            "provider": self.provider,
            "name": self.name,
            "avatar": self.avatar,
        }
