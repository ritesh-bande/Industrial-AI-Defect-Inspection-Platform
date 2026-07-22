from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.postgres import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # operator, quality_engineer, quality_manager, factory_supervisor, admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    prediction = Column(String, default="Pass")  # Pass or Fail
    defect_type = Column(String, default="none")  # scratch, crack, dent, missing_component, surface_damage, misalignment, none
    severity_level = Column(String, default="none")  # low, medium, high, none
    score = Column(Float, default=0.0)  # confidence score or anomaly score
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
    
    # Mongo document reference linking bounding boxes/annotations
    mongo_metadata_id = Column(String, nullable=True)

    # Relationships
    rework_tickets = relationship("ReworkTicket", back_populates="inspection", cascade="all, delete-orphan")

class ReworkTicket(Base):
    __tablename__ = "rework_tickets"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    ticket_number = Column(String, unique=True, nullable=False)
    status = Column(String, default="open")  # open, in_progress, completed
    notes = Column(Text, default="")
    priority = Column(String, default="Medium")  # Low, Medium, High
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="rework_tickets")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_type = Column(String, nullable=False)  # ai_model, manufacturing, system
    metric_name = Column(String, nullable=False)  # e.g., f1_score, yield_rate, cpu_usage
    metric_value = Column(Float, nullable=False)
    product_id = Column(String, nullable=True)
    production_line = Column(String, nullable=True)

class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g. line_1, line_2
    status = Column(Boolean, default=True)  # True = Active, False = Inactive
    description = Column(String, nullable=True)

class InspectionSession(Base):
    __tablename__ = "inspection_sessions"

    id = Column(Integer, primary_key=True, index=True)
    production_line_id = Column(Integer, ForeignKey("production_lines.id"), nullable=True)
    operator_name = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # active, completed
