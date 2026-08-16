import os
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from ai.inference import pipeline
from database.mongo import save_unstructured_metadata
from services.db_service import create_inspection_entry

logger = logging.getLogger("visioninspect.services")

# Folders configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEATMAP_DIR = os.path.join(BASE_DIR, "static", "heatmaps")
ANNOTATION_DIR = os.path.join(BASE_DIR, "static", "annotations")

def run_image_inspection(db: Session, file_path: str, filename: str, metadata: dict, active_model="yolo") -> dict:
    """
    Coordinates:
      1. AI inference (pre-processing + classification + heatmaps + annotations)
      2. Creating primary record in PostgreSQL database
      3. Creating unstructured details record in MongoDB database
      4. Linking databases together and returning results
    """
    # 1. Run AI detection pipeline
    result = pipeline.run_inference(
        image_path=file_path,
        save_heatmap_dir=HEATMAP_DIR,
        save_annotation_dir=ANNOTATION_DIR,
        active_model_type=active_model
    )
    
    # 2. Insert into PostgreSQL
    db_inspection = create_inspection_entry(
        db=db,
        filename=filename,
        prediction=result["prediction"],
        defect_type=result["defect_type"],
        severity_level=result["severity_level"],
        score=result["score"],
        heatmap_url=result["heatmap_url"],
        metadata=metadata
    )
    
    # 3. Insert unstructured details into MongoDB
    mongo_payload = result["mongo_data"]
    mongo_payload["inspection_id"] = db_inspection.id
    
    mongo_id = save_unstructured_metadata(
        inspection_id=db_inspection.id,
        data=mongo_payload
    )
    
    # 4. Link MongoDB ref back to PostgreSQL
    db_inspection.mongo_metadata_id = mongo_id
    db.commit()
    db.refresh(db_inspection)
    
    # 5. Build return payload matching InspectionResponse structure
    return {
        "id": db_inspection.id,
        "filename": db_inspection.filename,
        "prediction": db_inspection.prediction,
        "defect_type": db_inspection.defect_type,
        "severity_level": db_inspection.severity_level,
        "score": db_inspection.score,
        "heatmap_url": db_inspection.heatmap_url if db_inspection.heatmap_url else None,
        "image_url": f"/static/uploads/{db_inspection.filename}",
        "batch_number": db_inspection.batch_number,
        "product_id": db_inspection.product_id,
        "production_line": db_inspection.production_line,
        "shift": db_inspection.shift,
        "operator_name": db_inspection.operator_name,
        "review_status": db_inspection.review_status,
        "review_notes": db_inspection.review_notes,
        "created_at": db_inspection.created_at,
        "mongo_metadata_id": db_inspection.mongo_metadata_id
    }
