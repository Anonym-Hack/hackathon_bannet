import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Supplier")  # Supplier or Buyer
    city = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    listings = relationship("MaterialListing", back_populates="supplier", cascade="all, delete-orphan")
    requests = relationship("BuyerRequest", back_populates="buyer", cascade="all, delete-orphan")
    sent_inquiries = relationship("Inquiry", foreign_keys="Inquiry.buyer_id", back_populates="buyer")
    received_inquiries = relationship("Inquiry", foreign_keys="Inquiry.supplier_id", back_populates="supplier")


class MaterialListing(Base):
    __tablename__ = "material_listings"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # metal, plastic, chemical, etc.
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="kg")
    price_type = Column(String(50), nullable=False, default="fixed")  # fixed, free, negotiable
    price = Column(Float, nullable=False, default=0.0)
    location = Column(String(100), nullable=False, index=True)
    availability_status = Column(String(50), nullable=False, default="available")  # available, reserved, completed
    image_url = Column(String(500), nullable=True)

    # AI Material Analysis Output
    ai_material_name = Column(String(255), nullable=True)
    ai_composition = Column(Text, nullable=True)
    ai_condition = Column(String(100), nullable=True)
    ai_reuse_applications_json = Column(Text, nullable=True)  # JSON string list
    ai_target_industries_json = Column(Text, nullable=True)   # JSON string list
    ai_handling_notes = Column(Text, nullable=True)
    ai_sustainability_score = Column(Integer, nullable=False, default=70)  # 0 - 100
    ai_confidence = Column(String(50), nullable=False, default="High")
    ai_is_demo_mode = Column(Boolean, nullable=False, default=True)
    is_hazardous = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    supplier = relationship("User", back_populates="listings")
    inquiries = relationship("Inquiry", back_populates="listing", cascade="all, delete-orphan")

    @property
    def ai_reuse_applications(self):
        if self.ai_reuse_applications_json:
            try:
                return json.loads(self.ai_reuse_applications_json)
            except Exception:
                return []
        return []

    @property
    def ai_target_industries(self):
        if self.ai_target_industries_json:
            try:
                return json.loads(self.ai_target_industries_json)
            except Exception:
                return []
        return []


class BuyerRequest(Base):
    __tablename__ = "buyer_requests"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    material_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    quantity_needed = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="kg")
    location = Column(String(100), nullable=False)
    use_case = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="open")  # open, fulfilled, closed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    buyer = relationship("User", back_populates="requests")


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("material_listings.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="open")  # open, closed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    listing = relationship("MaterialListing", back_populates="inquiries")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="sent_inquiries")
    supplier = relationship("User", foreign_keys=[supplier_id], back_populates="received_inquiries")
    messages = relationship("Message", back_populates="inquiry", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    inquiry = relationship("Inquiry", back_populates="messages")
    sender = relationship("User")
