import os
import sys
import random
import logging

# Ensure project root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.postgres import init_db, get_db, SessionLocal
from database.mongo import save_unstructured_metadata
from utils.logging import setup_logging
from models.models import User, ProductionLine, Inspection, ReworkTicket
from authentication.jwt import get_password_hash

# 1. Initialize log handlers
setup_logging()
logger = logging.getLogger("visioninspect.main")

app = FastAPI(
    title="VisionInspect AI API",
    description="FastAPI modular backend supporting PostgreSQL, MongoDB, PyTorch, and YOLO.",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
HEATMAP_DIR = os.path.join(STATIC_DIR, "heatmaps")
ANNOTATION_DIR = os.path.join(STATIC_DIR, "annotations")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HEATMAP_DIR, exist_ok=True)
os.makedirs(ANNOTATION_DIR, exist_ok=True)

# Mount Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 2. Import modular routers
from routes.auth import router as auth_router
from routes.inspections import router as inspections_router
from routes.rework import router as rework_router
from routes.analytics import router as analytics_router
from routes.users import router as users_router
from routes.production import router as production_router
from routes.model import router as model_router
from routes.reports import router as reports_router
from routes.finetune import router as finetune_router

app.include_router(auth_router)
app.include_router(inspections_router)
app.include_router(rework_router)
app.include_router(analytics_router)
app.include_router(users_router)
app.include_router(production_router)
app.include_router(model_router)
app.include_router(reports_router)
app.include_router(finetune_router)

# 3. Seed script on startup
def seed_data():
    db = SessionLocal()
    try:
        # User seeding
        admin_pass = os.getenv("ADMIN_INITIAL_PASSWORD", "Admin@Vision2026!")
        operator_pass = os.getenv("OPERATOR_INITIAL_PASSWORD", "VisionInspect@Op2026")

        admin_user = db.query(User).filter((User.username == "Quality Engineer") | (User.email == "admin@visioninspect.ai")).first()
        if not admin_user:
            admin_user = User(
                username="Quality Engineer",
                email="admin@visioninspect.ai",
                hashed_password=get_password_hash(admin_pass),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            logger.info("Seeding default admin user.")
        else:
            admin_user.hashed_password = get_password_hash(admin_pass)
            admin_user.is_active = True
            db.add(admin_user)
            
        operator_user = db.query(User).filter((User.username == "operator") | (User.email == "operator@visioninspect.ai")).first()
        if not operator_user:
            operator_user = User(
                username="operator",
                email="operator@visioninspect.ai",
                hashed_password=get_password_hash(operator_pass),
                role="operator",
                is_active=True
            )
            db.add(operator_user)
        else:
            operator_user.hashed_password = get_password_hash(operator_pass)
            operator_user.is_active = True
            db.add(operator_user)
            
        db.commit()
            
        # Production Lines seeding
        lines = db.query(ProductionLine).all()
        if not lines:
            line1 = ProductionLine(name="Assembly Line Alpha", code="line_1", status=True, description="Primary manufacturing line")
            line2 = ProductionLine(name="Inspection Conveyor Beta", code="line_2", status=True, description="Secondary verification conveyor")
            line3 = ProductionLine(name="Packaging Line Gamma", code="line_3", status=True, description="End of line wrapping station")
            db.add(line1)
            db.add(line2)
            db.add(line3)
            logger.info("Seeding default production lines.")
            db.commit()
            
        # Seed simulated inspections for charts if empty
        inspections_count = db.query(Inspection).count()
        if inspections_count == 0:
            logger.info("Seeding simulated historical inspection records in Postgre & Mongo.")
            products = ["bottle", "cable", "tile", "leather"]
            lines = ["line_1", "line_2", "line_3"]
            defect_types = ["scratch", "crack", "dent", "missing_component", "surface_damage", "misalignment"]
            severities = ["low", "medium", "high"]
            
            base_time = datetime.utcnow() - timedelta(days=10)
            
            for d in range(11):
                day = base_time + timedelta(days=d)
                # Seed 10-15 inspections per day
                num_inspections = random.randint(10, 15)
                for i in range(num_inspections):
                    is_pass = random.random() > 0.12 # 12% defect rate
                    prediction = "Pass" if is_pass else "Fail"
                    defect = "none" if is_pass else random.choice(defect_types)
                    severity = "none" if is_pass else random.choice(severities)
                    score = float(random.uniform(0.5, 3.8)) if is_pass else float(random.uniform(4.5, 9.8))
                    
                    # Create entry
                    item = Inspection(
                        filename=f"seed_{d}_{i}.png",
                        prediction=prediction,
                        defect_type=defect,
                        severity_level=severity,
                        score=score,
                        heatmap_url=f"/static/heatmaps/seed_{d}_{i}.png" if not is_pass else None,
                        batch_number=f"BAT-{day.strftime('%y%m%d')}-{random.randint(10, 99)}",
                        product_id=random.choice(products),
                        production_line=random.choice(lines),
                        shift=f"Shift {random.choice(['A', 'B', 'C'])}",
                        operator_name=random.choice(["Quality Engineer", "operator"]),
                        review_status="approved" if is_pass else random.choice(["approved", "sent_for_rework", "manual_review"]),
                        review_notes="Automatic Pass." if is_pass else "Defect verified.",
                        created_at=day
                    )
                    db.add(item)
                    db.commit()
                    db.refresh(item)
                    
                    # Store MongoDB details
                    mongo_data = {
                        "inspection_id": item.id,
                        "prediction": prediction,
                        "defect_type": defect,
                        "severity_level": severity,
                        "confidence_score": score / 10.0,
                        "bounding_boxes": [[50, 50, 150, 150]] if not is_pass else [],
                        "processing_speed_ms": random.randint(30, 80),
                        "pipeline_logs": [
                            "Inference pipeline triggered.",
                            "CLAHE contrast enhancement applied.",
                            "Canny edge detection performed.",
                            "AI Classification complete."
                        ],
                        "timestamp": day.isoformat()
                    }
                    mongo_id = save_unstructured_metadata(item.id, mongo_data)
                    item.mongo_metadata_id = mongo_id
                    
                    # Create Rework Ticket if sent for rework
                    if item.review_status == "sent_for_rework":
                        ticket = ReworkTicket(
                            inspection_id=item.id,
                            ticket_number=f"RWK-{item.id}-{random.randint(1000, 9999)}",
                            status=random.choice(["open", "in_progress", "completed"]),
                            notes="Needs surface polishing.",
                            priority=random.choice(["Low", "Medium", "High"]),
                            created_at=day
                        )
                        db.add(ticket)
            logger.info("Historical seed finished successfully.")
            db.commit()
            
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()

# Initialize DB tables
init_db()
seed_data()

@app.get("/health", tags=["Health"])
def health_check():
    """
    Returns API runtime health, real DB connectivity, and active AI components statuses.
    """
    from utils.system_stats import get_system_metrics
    try:
        sys_metrics = get_system_metrics()
    except Exception:
        sys_metrics = {}

    # Check model loading status
    try:
        from ai.inference import classification_model, segmentation_model, YOLO_AVAILABLE
    except Exception:
        classification_model = None
        segmentation_model = None
        YOLO_AVAILABLE = False

    # PostgreSQL / SQLite connectivity check
    postgres_status = "connected"
    postgres_type = "postgresql"
    try:
        import sqlalchemy
        from database.postgres import SessionLocal as _SL, DATABASE_URL as _DB_URL
        if "sqlite" in _DB_URL:
            postgres_type = "sqlite"
        _db = _SL()
        _db.execute(sqlalchemy.text("SELECT 1"))
        _db.close()
    except Exception as _e:
        postgres_status = "disconnected"
        postgres_type = "unknown"

    # MongoDB / file-fallback connectivity check
    mongo_status = "connected"
    mongo_type = "mongodb"
    try:
        from database.mongo import db_client as _mc, is_mock as _im
        if _im or _mc is None:
            mongo_type = "file_fallback"
        else:
            _mc.admin.command("ping")
    except Exception:
        mongo_status = "disconnected"
        mongo_type = "unknown"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": postgres_status,
        "postgres": postgres_status,
        "postgres_type": postgres_type,
        "mongo": mongo_status,
        "mongo_type": mongo_type,
        "system": sys_metrics,
        "artifacts": {
            "padim_checkpoint": True,
            "defect_classifier": classification_model is not None,
            "baseline_reference": True,
            "segmentation_model": segmentation_model is not None,
            "yolo_library": YOLO_AVAILABLE
        }
    }
@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirects route root requests directly to FastAPI OpenAPI docs"""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
