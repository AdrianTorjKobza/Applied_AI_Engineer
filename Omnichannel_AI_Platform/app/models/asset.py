import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

class AssetType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    content = Column(Text, nullable=False) # Stores text or the local file path for images
    created_at = Column(DateTime, default=datetime.utcnow)

    # Bi-directional relationship back to the Job
    job = relationship("Job", back_populates="assets")
    
    # One-to-One relationship to Metadata
    metadata_item = relationship("Metadata", back_populates="asset", uselist=False, cascade="all, delete-orphan")

class Metadata(Base):
    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    seo_tags = Column(Text, nullable=True) # Stored as a JSON string
    alt_text = Column(String, nullable=True)
    json_ld = Column(Text, nullable=True) # Stored as a JSON string

    # Bi-directional relationship back to the Asset
    asset = relationship("Asset", back_populates="metadata_item")