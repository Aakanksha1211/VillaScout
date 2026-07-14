from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from villascout.database.base import Base


class VillaRecord(Base):
    __tablename__ = "villas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contact: Mapped["ContactRecord"] = relationship(
        back_populates="villa", cascade="all, delete-orphan", uselist=False
    )
    amenities: Mapped[list["AmenityRecord"]] = relationship(
        back_populates="villa", cascade="all, delete-orphan"
    )
    prices: Mapped[list["PriceRecord"]] = relationship(
        back_populates="villa", cascade="all, delete-orphan"
    )
    source_listings: Mapped[list["SourceListingRecord"]] = relationship(
        back_populates="villa", cascade="all, delete-orphan"
    )
    review_summary: Mapped["ReviewSummaryRecord"] = relationship(
        back_populates="villa", cascade="all, delete-orphan", uselist=False
    )


class ContactRecord(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    villa_id: Mapped[int] = mapped_column(ForeignKey("villas.id"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(Text)
    whatsapp: Mapped[str | None] = mapped_column(String(100))
    instagram: Mapped[str | None] = mapped_column(Text)

    villa: Mapped[VillaRecord] = relationship(back_populates="contact")


class AmenityRecord(Base):
    __tablename__ = "amenities"
    __table_args__ = (UniqueConstraint("villa_id", "name", name="uq_amenity_villa_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    villa_id: Mapped[int] = mapped_column(ForeignKey("villas.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str | None] = mapped_column(String(255))

    villa: Mapped[VillaRecord] = relationship(back_populates="amenities")


class PriceRecord(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    villa_id: Mapped[int] = mapped_column(ForeignKey("villas.id"))
    amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    unit: Mapped[str | None] = mapped_column(String(100))
    raw_text: Mapped[str | None] = mapped_column(Text)

    villa: Mapped[VillaRecord] = relationship(back_populates="prices")


class SourceListingRecord(Base):
    __tablename__ = "source_listings"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_listing_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    villa_id: Mapped[int] = mapped_column(ForeignKey("villas.id"))
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    villa: Mapped[VillaRecord] = relationship(back_populates="source_listings")


class ReviewSummaryRecord(Base):
    __tablename__ = "review_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    villa_id: Mapped[int] = mapped_column(ForeignKey("villas.id"), unique=True)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)

    villa: Mapped[VillaRecord] = relationship(back_populates="review_summary")
