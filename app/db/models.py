from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, DateTime, Text
from datetime import datetime, timezone
from typing import Optional
import uuid


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    )

    # Relationship — позволяет делать user.products
    products: Mapped[list["Product"]] = relationship(back_populates="user")
    reports: Mapped[list["Report"]] = relationship(back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    )

    # Relationship — позволяет делать product.user
    user: Mapped["User"] = relationship(back_populates="products")
    reports: Mapped[list["Report"]] = relationship(back_populates="product")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    )

    # Relationship — позволяет делать product.user
    user: Mapped["User"] = relationship(back_populates="reports")
    product: Mapped[Optional["Product"]] = relationship(back_populates="reports")