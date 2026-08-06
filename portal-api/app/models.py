"""Portal data model: users + modular RBAC (roles / features / permissions).

Permissions are modular CRUD per feature per role: one ``Permission`` row holds
the four booleans for a (role, feature) pair. A user's effective permissions are
the OR of the rows across all their roles (see ``rbac.effective_permissions``).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

# Association: which roles a user holds.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


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


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(String(512), default="")


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("role_id", "feature_id", name="uq_role_feature"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    feature_id: Mapped[int] = mapped_column(
        ForeignKey("features.id", ondelete="CASCADE"), index=True
    )
    can_create: Mapped[bool] = mapped_column(Boolean, default=False)
    can_read: Mapped[bool] = mapped_column(Boolean, default=False)
    can_update: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)

    def granted_actions(self) -> list[str]:
        out = []
        if self.can_create:
            out.append("create")
        if self.can_read:
            out.append("read")
        if self.can_update:
            out.append("update")
        if self.can_delete:
            out.append("delete")
        return out

    def apply_actions(self, actions: set[str]) -> None:
        self.can_create = "create" in actions
        self.can_read = "read" in actions
        self.can_update = "update" in actions
        self.can_delete = "delete" in actions
