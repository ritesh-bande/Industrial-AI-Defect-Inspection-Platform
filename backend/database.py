import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visioninspect.db")

# If using PostgreSQL, verify driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # operator, quality_manager, admin, factory_supervisor
    created_at = Column(DateTime, default=datetime.utcnow)

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    prediction = Column(String, default="Pass")  # Pass or Fail
    defect_type = Column(String, default="none")  # e.g. crack, scratch, broken, good
    severity_level = Column(String, default="low")  # low, medium, high, none
    score = Column(Float, default=0.0)  # Anomaly score from model
    heatmap_url = Column(String, nullable=True)
    
    # Metadata Form
    batch_number = Column(String, default="")
    product_id = Column(String, default="")
    production_line = Column(String, default="")
    shift = Column(String, default="")
    operator_name = Column(String, default="")
    
    # Review status
    review_status = Column(String, default="ai_completed")  # ai_completed, manual_review, approved, rejected, sent_for_rework
    review_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to rework tickets
    rework_tickets = relationship("ReworkTicket", back_populates="inspection", cascade="all, delete-orphan")

class ReworkTicket(Base):
    __tablename__ = "rework_tickets"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    ticket_number = Column(String, unique=True, nullable=False)
    status = Column(String, default="open")  # open, in_progress, completed
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="rework_tickets")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
