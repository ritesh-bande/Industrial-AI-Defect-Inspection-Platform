import os
import shutil
import random
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import jwt

from database import init_db, get_db, User, Inspection, ReworkTicket
from security import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM
from ai_model import detector

app = FastAPI(
    title="VisionInspect AI API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
HEATMAP_DIR = os.path.join(BASE_DIR, "static", "heatmaps")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HEATMAP_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Database initialization
init_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        # For development ease, if auth header is missing, return a default mock user
        # to prevent strict blocking while front-ends integrate.
        mock_user = db.query(User).filter(User.username == "admin").first()
        if not mock_user:
            mock_user = User(username="admin", email="admin@factory.com", hashed_password=get_password_hash("admin"), role="admin")
            db.add(mock_user)
            db.commit()
            db.refresh(mock_user)
        return mock_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ROUTES ---

@app.post("/api/auth/register", status_code=201)
def register(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username") or payload.get("name", "")
    username = username.strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip()
    role = payload.get("role", "operator").strip()

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Username, email, and password are required")

    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    hashed_pw = get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_pw, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username})
    return {
        "message": "registered",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": new_user.id, "username": new_user.username, "email": new_user.email, "role": new_user.role}
    }

@app.post("/api/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip()

    if not password or (not username and not email):
        raise HTTPException(
            status_code=400,
            detail="Username/email and password are required"
        )

    if email:
        user = db.query(User).filter(User.email == email).first()
    else:
        user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password"
        )

    token = create_access_token({"sub": user.username})

    return {
        "message": "logged in",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@app.get("/api/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }

# --- INSPECTIONS ---

@app.get("/api/inspections")
def list_inspections(
    skip: int = 0,
    limit: int = 50,
    product_id: Optional[str] = None,
    production_line: Optional[str] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
    if production_line:
        query = query.filter(Inspection.production_line == production_line)
    if review_status:
        query = query.filter(Inspection.review_status == review_status)

    total = query.count()
    items = query.order_by(Inspection.created_at.desc()).offset(skip).limit(limit).all()
    
    # Map model instances to match frontend keys
    mapped_items = []
    for item in items:
        mapped_items.append({
            "id": item.id,
            "filename": item.filename,
            "prediction": item.prediction,
            "defect_type": item.defect_type,
            "severity_level": item.severity_level,
            "score": item.score,
            "heatmap_url": f"http://localhost:8000{item.heatmap_url}" if item.heatmap_url else None,
            "image_url": f"http://localhost:8000/static/uploads/{item.filename}",
            "batch_number": item.batch_number,
            "product_id": item.product_id,
            "production_line": item.production_line,
            "shift": item.shift,
            "operator_name": item.operator_name,
            "review_status": item.review_status,
            "review_notes": item.review_notes,
            "created_at": item.created_at.isoformat()
        })
    return {"total": total, "items": mapped_items}

@app.post("/api/inspections/inspect")
def inspect_image(
    file: UploadFile = File(...),
    batch_number: Optional[str] = None,
    product_id: Optional[str] = None,
    production_line: Optional[str] = None,
    shift: Optional[str] = None,
    operator_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Save file
    safe_filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run AI Detection
    prediction, defect_type, severity, score, heatmap_path = detector.inspect(file_path, save_heatmap_dir=HEATMAP_DIR)

    # Create Database Entry
    new_inspection = Inspection(
        filename=safe_filename,
        prediction=prediction,
        defect_type=defect_type,
        severity_level=severity,
        score=score,
        heatmap_url=heatmap_path,
        batch_number=batch_number or "",
        product_id=product_id or "",
        production_line=production_line or "",
        shift=shift or "",
        operator_name=operator_name or "",
        review_status="ai_completed"
    )
    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    return {
        "id": new_inspection.id,
        "filename": new_inspection.filename,
        "prediction": new_inspection.prediction,
        "defect_type": new_inspection.defect_type,
        "severity_level": new_inspection.severity_level,
        "score": new_inspection.score,
        "heatmap_url": f"http://localhost:8000{new_inspection.heatmap_url}" if new_inspection.heatmap_url else None,
        "image_url": f"http://localhost:8000/static/uploads/{new_inspection.filename}",
        "batch_number": new_inspection.batch_number,
        "product_id": new_inspection.product_id,
        "production_line": new_inspection.production_line,
        "shift": new_inspection.shift,
        "operator_name": new_inspection.operator_name,
        "review_status": new_inspection.review_status,
        "review_notes": new_inspection.review_notes,
        "created_at": new_inspection.created_at.isoformat()
    }

@app.patch("/api/inspections/{inspection_id}/review-status")
def update_review_status(inspection_id: int, payload: dict, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    status = payload.get("review_status")
    notes = payload.get("review_notes", "")

    if status not in ["approved", "rejected", "sent_for_rework", "manual_review"]:
        raise HTTPException(status_code=400, detail="Invalid review status")

    inspection.review_status = status
    inspection.review_notes = notes

    ticket_id = None
    ticket_number = None
    ticket_status = None

    if status == "sent_for_rework":
        # Create rework ticket
        ticket_number = f"RWK-{inspection.id}-{random.randint(1000, 9999)}"
        new_ticket = ReworkTicket(
            inspection_id=inspection.id,
            ticket_number=ticket_number,
            status="open",
            notes=notes
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        ticket_id = new_ticket.id
        ticket_status = new_ticket.status

    db.commit()
    db.refresh(inspection)

    return {
        "id": inspection.id,
        "review_status": inspection.review_status,
        "review_notes": inspection.review_notes,
        "rework_ticket_id": ticket_id,
        "rework_ticket_number": ticket_number,
        "rework_ticket_status": ticket_status
    }

@app.get("/api/inspections/{inspection_id}")
def get_single_inspection(inspection_id: int, db: Session = Depends(get_db)):
    item = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    return {
        "id": item.id,
        "filename": item.filename,
        "prediction": item.prediction,
        "defect_type": item.defect_type,
        "severity_level": item.severity_level,
        "score": item.score,
        "heatmap_url": f"http://localhost:8000{item.heatmap_url}" if item.heatmap_url else None,
        "image_url": f"http://localhost:8000/static/uploads/{item.filename}",
        "batch_number": item.batch_number,
        "product_id": item.product_id,
        "production_line": item.production_line,
        "shift": item.shift,
        "operator_name": item.operator_name,
        "review_status": item.review_status,
        "review_notes": item.review_notes,
        "created_at": item.created_at.isoformat()
    }

# --- ANALYTICS ---

@app.get("/api/analytics/summary")
def get_analytics_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    production_line: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)
    if production_line:
        query = query.filter(Inspection.production_line == production_line)
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
        
    total_inspections = query.count()
    passed = query.filter(Inspection.prediction == "Pass").count()
    failed = query.filter(Inspection.prediction == "Fail").count()
    
    defect_types = {}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "none": 0}
    
    inspections = query.all()
    for item in inspections:
        defect_types[item.defect_type] = defect_types.get(item.defect_type, 0) + 1
        severity_counts[item.severity_level] = severity_counts.get(item.severity_level, 0) + 1
        
    return {
        "summary": {
            "total_inspections": total_inspections,
            "passed": passed,
            "failed": failed,
            "yield_rate": round((passed / total_inspections * 100), 2) if total_inspections > 0 else 100.0
        },
        "defect_distribution": defect_types,
        "severity_distribution": severity_counts
    }

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):

    total_inspections = db.query(Inspection).count()
    passed = db.query(Inspection).filter(Inspection.prediction == "Pass").count()
    failed = db.query(Inspection).filter(Inspection.prediction == "Fail").count()
    
    # Calculate defect rates by category/product
    defect_types = {}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "none": 0}
    
    inspections = db.query(Inspection).all()
    for item in inspections:
        defect_types[item.defect_type] = defect_types.get(item.defect_type, 0) + 1
        severity_counts[item.severity_level] = severity_counts.get(item.severity_level, 0) + 1

    return {
        "summary": {
            "total_inspections": total_inspections,
            "passed": passed,
            "failed": failed,
            "yield_rate": round((passed / total_inspections * 100), 2) if total_inspections > 0 else 100.0
        },
        "defect_distribution": defect_types,
        "severity_distribution": severity_counts
    }

# --- CATALOG & REWORK TICKETS ---

@app.get("/api/production/catalog")
def get_catalog():
    # Return sample/mock metadata option catalogs matching frontend selections
    return {
        "products": [
            {"product_id": "bottle", "name": "MVTec Bottle"},
            {"product_id": "cable", "name": "MVTec Cable"},
            {"product_id": "carpet", "name": "MVTec Carpet"},
            {"product_id": "leather", "name": "MVTec Leather"},
            {"product_id": "tile", "name": "MVTec Tile"}
        ],
        "production_lines": [
            {"line_id": "line_1", "name": "Assembly Line Alpha"},
            {"line_id": "line_2", "name": "Inspection Conveyor Beta"},
            {"line_id": "line_3", "name": "Packaging Line Gamma"}
        ]
    }

@app.get("/api/rework/tickets/by-inspection/{inspection_id}")
def get_rework_ticket_by_inspection(inspection_id: int, db: Session = Depends(get_db)):
    ticket = db.query(ReworkTicket).filter(ReworkTicket.inspection_id == inspection_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Rework ticket not found")
    return {
        "id": ticket.id,
        "inspection_id": ticket.inspection_id,
        "ticket_number": ticket.ticket_number,
        "status": ticket.status,
        "notes": ticket.notes,
        "created_at": ticket.created_at.isoformat()
    }

@app.patch("/api/rework/tickets/{ticket_id}")
def update_rework_ticket(ticket_id: int, payload: dict, db: Session = Depends(get_db)):
    ticket = db.query(ReworkTicket).filter(ReworkTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Rework ticket not found")
    
    if "status" in payload:
        ticket.status = payload["status"]
    if "notes" in payload:
        ticket.notes = payload["notes"]
        
    db.commit()
    db.refresh(ticket)
    return {
        "id": ticket.id,
        "inspection_id": ticket.inspection_id,
        "ticket_number": ticket.ticket_number,
        "status": ticket.status,
        "notes": ticket.notes,
        "created_at": ticket.created_at.isoformat()
    }

@app.get("/api/rework/tickets")
def list_rework_tickets(db: Session = Depends(get_db)):
    tickets = db.query(ReworkTicket).order_by(ReworkTicket.created_at.desc()).all()
    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "inspection_id": t.inspection_id,
            "ticket_number": t.ticket_number,
            "status": t.status,
            "notes": t.notes,
            "created_at": t.created_at.isoformat()
        })
    return result


@app.post("/api/reports/inspection/{inspection_id}")
def create_report(inspection_id: int, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return {
        "id": f"REP-{inspection.id}-{random.randint(100, 999)}",
        "inspection_id": inspection.id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "generated"
    }

@app.get("/api/reports")
def list_reports(db: Session = Depends(get_db)):
    # Return placeholder generated reports
    return []

@app.get("/api/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users]

@app.post("/api/users")
def create_user(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip()
    role = payload.get("role", "operator").strip()
    print("Username:", username)
    print("Email:", email)
    print("Password:", password)
    print("Password type:", type(password))
    print("Password length:", len(password))
    hashed_pw = get_password_hash(password)

    user = User(username=username, email=email, hashed_password=hashed_pw, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}

@app.patch("/api/users/{user_id}")
def update_user(user_id: int, payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "role" in payload:
        user.role = payload["role"]
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}

@app.post("/api/users/{user_id}/reset-password")
def reset_password(user_id: int, payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    password = payload.get("password")
    user.hashed_password = get_password_hash(password)
    db.commit()
    return {"message": "password reset successfully"}

@app.get("/api/audit-logs")
def list_audit_logs(limit: int = 50):
    return []

@app.get("/api/model/metrics")
def get_model_metrics():
    return {
        "accuracy": 0.942,
        "precision": 0.931,
        "recall": 0.950,
        "f1_score": 0.940,
        "threshold": 0.45
    }

@app.get("/api/model/settings")
def get_model_settings():
    return {"threshold": 0.45, "resolution": 224}

@app.patch("/api/model/settings")
def update_model_settings(payload: dict):
    return {"status": "updated", "settings": payload}

@app.get("/api/inspections/camera-samples")
def get_camera_samples():


    # Helper endpoint mimicking industrial live camera sample categories
    return [
        {"id": "sample1", "label": "MVTec Bottle - Good", "product_id": "bottle"},
        {"id": "sample2", "label": "MVTec Bottle - Defect", "product_id": "bottle"},
        {"id": "sample3", "label": "MVTec Cable - Defect", "product_id": "cable"}
    ]

# Static server setup check
@app.get("/")
def root():
    return {"status": "running", "service": "VisionInspect AI FastAPI Server"}
