import os
import shutil
import random
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.postgres import get_db
from models.models import User, Inspection
from models.schemas import InspectionResponse, InspectionUpdate, InspectionMetadataUpdate
from authentication.jwt import get_current_user
from authentication.roles import require_engineer, require_supervisor
from services.db_service import (
    list_inspections,
    count_inspections,
    get_inspection_by_id,
    update_inspection_status,
    update_inspection_metadata,
    create_rework_ticket
)
from services.ai_service import run_image_inspection

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])

# Local upload directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=dict)
def get_inspections_list(
    skip: int = 0,
    limit: int = 50,
    product_id: Optional[str] = None,
    production_line: Optional[str] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List inspection records with pagination and filters.
    """
    items = list_inspections(db, skip, limit, product_id, production_line, review_status)
    total = count_inspections(db, product_id, production_line, review_status)
    
    # Map items to match frontend image and heatmap URL schemes
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
            "created_at": item.created_at,
            "mongo_metadata_id": item.mongo_metadata_id
        })
    return {"total": total, "items": mapped_items}

@router.post("/inspect")
def inspect_uploaded_image(
    file: UploadFile = File(...),
    batch_number: Optional[str] = "",
    product_id: Optional[str] = "",
    production_line: Optional[str] = "",
    shift: Optional[str] = "",
    operator_name: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and immediately run AI inspection.
    """
    # Safe save
    safe_filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    metadata = {
        "batch_number": batch_number,
        "product_id": product_id,
        "production_line": production_line,
        "shift": shift,
        "operator_name": operator_name or current_user.username
    }
    
    # Run the service coordination
    result = run_image_inspection(db, file_path, safe_filename, metadata)
    return result

@router.post("/upload")
def upload_only(
    file: UploadFile = File(...),
    batch_number: Optional[str] = "",
    product_id: Optional[str] = "",
    production_line: Optional[str] = "",
    shift: Optional[str] = "",
    operator_name: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compatibility endpoint: handles raw upload and runs inspection immediately.
    """
    return inspect_uploaded_image(
        file=file,
        batch_number=batch_number,
        product_id=product_id,
        production_line=production_line,
        shift=shift,
        operator_name=operator_name,
        db=db,
        current_user=current_user
    )

@router.post("/batch-inspect")
def batch_inspect_images(
    files: List[UploadFile] = File(...),
    batch_number: Optional[str] = "",
    product_id: Optional[str] = "",
    production_line: Optional[str] = "",
    shift: Optional[str] = "",
    operator_name: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run batch AI inspection on multiple images.
    """
    results = []
    for file in files:
        safe_filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        metadata = {
            "batch_number": batch_number,
            "product_id": product_id,
            "production_line": production_line,
            "shift": shift,
            "operator_name": operator_name or current_user.username
        }
        
        res = run_image_inspection(db, file_path, safe_filename, metadata)
        results.append(res)
    return results

@router.get("/{inspection_id}")
def get_single_inspection(
    inspection_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details of a single inspection.
    """
    item = get_inspection_by_id(db, inspection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
        
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
        "created_at": item.created_at,
        "mongo_metadata_id": item.mongo_metadata_id
    }

@router.patch("/{inspection_id}/review-status")
def update_inspection_review_status(
    inspection_id: int,
    payload: InspectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """
    Update the manual review decision of an inspection.
    If the status is 'sent_for_rework', automatically creates a Rework Ticket.
    """
    item = get_inspection_by_id(db, inspection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
        
    status = payload.review_status
    notes = payload.review_notes
    
    if status not in ["approved", "rejected", "sent_for_rework", "manual_review"]:
        raise HTTPException(status_code=400, detail="Invalid review status parameter.")
        
    updated = update_inspection_status(db, inspection_id, status, notes)
    
    ticket_id = None
    ticket_number = None
    ticket_status = None
    
    if status == "sent_for_rework":
        ticket = create_rework_ticket(db, inspection_id=inspection_id, notes=notes)
        ticket_id = ticket.id
        ticket_number = ticket.ticket_number
        ticket_status = ticket.status
        
    return {
        "id": updated.id,
        "review_status": updated.review_status,
        "review_notes": updated.review_notes,
        "rework_ticket_id": ticket_id,
        "rework_ticket_number": ticket_number,
        "rework_ticket_status": ticket_status
    }

@router.patch("/{inspection_id}/metadata")
def update_inspection_metadata_endpoint(
    inspection_id: int,
    payload: InspectionMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """
    Updates the production metadata associated with an inspection.
    """
    updated = update_inspection_metadata(db, inspection_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
    return updated

@router.get("/camera-samples")
def get_samples():
    """
    Returns industrial mock live camera sample options.
    """
    return [
        {"id": "sample1", "label": "MVTec Bottle - Good", "product_id": "bottle"},
        {"id": "sample2", "label": "MVTec Bottle - Defect (Contamination)", "product_id": "bottle"},
        {"id": "sample3", "label": "MVTec Cable - Defect (Missing Component)", "product_id": "cable"}
    ]

@router.post("/camera-simulate")
def simulate_camera_capture(
    frame_index: int = Query(0),
    label: Optional[str] = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates a live industrial camera feed capture and processes it.
    """
    # Pick a random sample image from our MVTec local dataset if available,
    # otherwise fallback to copying binary_bottle.png or gray_bottle.png
    bottle_good = "gray_bottle.png"
    bottle_defect = "binary_bottle.png"
    
    selected_image = bottle_good
    if label == "defect" or frame_index % 2 == 1:
        selected_image = bottle_defect
        
    if not os.path.exists(selected_image):
        # Create a mock black image with text if files not found
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        text = "MOCK GOOD" if selected_image == bottle_good else "MOCK DEFECT CONTAMINATION"
        cv2.putText(img, text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        temp_path = os.path.join(UPLOAD_DIR, "mock_captured.png")
        cv2.imwrite(temp_path, img)
        selected_image = temp_path
        
    # Copy file to upload directory
    safe_filename = f"capture_{int(datetime.utcnow().timestamp())}_{os.path.basename(selected_image)}"
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)
    shutil.copy(selected_image, dest_path)
    
    metadata = {
        "batch_number": f"BATCH-CAM-{random.randint(10, 99)}",
        "product_id": "bottle",
        "production_line": "line_1",
        "shift": "Shift A",
        "operator_name": current_user.username
    }
    
    result = run_image_inspection(db, dest_path, safe_filename, metadata)
    return result
