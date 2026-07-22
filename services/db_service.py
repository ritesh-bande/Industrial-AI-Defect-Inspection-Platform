import random
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import List, Optional

from models.models import User, Inspection, ReworkTicket, ProductionLine, Analytics
from models.schemas import UserCreate, InspectionCreate, ReworkTicketCreate, ProductionLineCreate
from authentication.jwt import get_password_hash

# --- USER CRUD ---
def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_pw = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def list_users(db: Session) -> List[User]:
    return db.query(User).all()

# --- INSPECTION CRUD ---
def create_inspection_entry(db: Session, filename: str, prediction: str, defect_type: str, severity_level: str, score: float, heatmap_url: str, metadata: dict, mongo_metadata_id: str = None) -> Inspection:
    db_inspection = Inspection(
        filename=filename,
        prediction=prediction,
        defect_type=defect_type,
        severity_level=severity_level,
        score=score,
        heatmap_url=heatmap_url,
        batch_number=metadata.get("batch_number", ""),
        product_id=metadata.get("product_id", ""),
        production_line=metadata.get("production_line", ""),
        shift=metadata.get("shift", ""),
        operator_name=metadata.get("operator_name", ""),
        review_status="ai_completed",
        mongo_metadata_id=mongo_metadata_id
    )
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def get_inspection_by_id(db: Session, idx: int) -> Optional[Inspection]:
    return db.query(Inspection).filter(Inspection.id == idx).first()

def list_inspections(db: Session, skip=0, limit=50, product_id="", production_line="", review_status="") -> List[Inspection]:
    query = db.query(Inspection)
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
    if production_line:
        query = query.filter(Inspection.production_line == production_line)
    if review_status:
        query = query.filter(Inspection.review_status == review_status)
    return query.order_by(desc(Inspection.created_at)).offset(skip).limit(limit).all()

def count_inspections(db: Session, product_id="", production_line="", review_status="") -> int:
    query = db.query(Inspection)
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
    if production_line:
        query = query.filter(Inspection.production_line == production_line)
    if review_status:
        query = query.filter(Inspection.review_status == review_status)
    return query.count()

def update_inspection_status(db: Session, inspection_id: int, review_status: str, review_notes: str) -> Optional[Inspection]:
    db_inspection = get_inspection_by_id(db, inspection_id)
    if not db_inspection:
        return None
    db_inspection.review_status = review_status
    db_inspection.review_notes = review_notes
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def update_inspection_metadata(db: Session, inspection_id: int, meta: dict) -> Optional[Inspection]:
    db_inspection = get_inspection_by_id(db, inspection_id)
    if not db_inspection:
        return None
    if "batch_number" in meta and meta["batch_number"] is not None:
        db_inspection.batch_number = meta["batch_number"]
    if "product_id" in meta and meta["product_id"] is not None:
        db_inspection.product_id = meta["product_id"]
    if "production_line" in meta and meta["production_line"] is not None:
        db_inspection.production_line = meta["production_line"]
    if "shift" in meta and meta["shift"] is not None:
        db_inspection.shift = meta["shift"]
    if "operator_name" in meta and meta["operator_name"] is not None:
        db_inspection.operator_name = meta["operator_name"]
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

# --- REWORK TICKET CRUD ---
def create_rework_ticket(db: Session, inspection_id: int, notes: str = "", priority: str = "Medium") -> ReworkTicket:
    # Generate unique ticket number
    ticket_number = f"RWK-{inspection_id}-{random.randint(1000, 9999)}"
    db_ticket = ReworkTicket(
        inspection_id=inspection_id,
        ticket_number=ticket_number,
        status="open",
        notes=notes,
        priority=priority
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_rework_ticket_by_id(db: Session, idx: int) -> Optional[ReworkTicket]:
    return db.query(ReworkTicket).filter(ReworkTicket.id == idx).first()

def get_rework_ticket_by_inspection_id(db: Session, inspection_id: int) -> Optional[ReworkTicket]:
    return db.query(ReworkTicket).filter(ReworkTicket.inspection_id == inspection_id).first()

def list_rework_tickets(db: Session) -> List[ReworkTicket]:
    return db.query(ReworkTicket).order_by(desc(ReworkTicket.created_at)).all()

def update_rework_ticket(db: Session, ticket_id: int, payload: dict) -> Optional[ReworkTicket]:
    db_ticket = get_rework_ticket_by_id(db, ticket_id)
    if not db_ticket:
        return None
    if "status" in payload and payload["status"] is not None:
        db_ticket.status = payload["status"]
    if "notes" in payload and payload["notes"] is not None:
        db_ticket.notes = payload["notes"]
    if "priority" in payload and payload["priority"] is not None:
        db_ticket.priority = payload["priority"]
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

# --- PRODUCTION LINE CRUD ---
def create_production_line_entry(db: Session, line_in: ProductionLineCreate) -> ProductionLine:
    db_line = ProductionLine(
        name=line_in.name,
        code=line_in.code,
        status=line_in.status,
        description=line_in.description
    )
    db.add(db_line)
    db.commit()
    db.refresh(db_line)
    return db_line

def list_production_lines(db: Session) -> List[ProductionLine]:
    return db.query(ProductionLine).all()
