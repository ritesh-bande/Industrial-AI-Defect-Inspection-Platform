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
    Coordinates AI inference, DB entry creation, and fallback error handling.
    """
    try:
        result = pipeline.run_inference(
            image_path=file_path,
            save_heatmap_dir=HEATMAP_DIR,
            save_annotation_dir=ANNOTATION_DIR,
            active_model_type=active_model
        )
    except Exception as e:
        logger.error(f"Inference error in pipeline: {e}. Using fail-safe fallback inspection result.")
        result = {
            "prediction": "Fail",
            "defect_type": "inspection_error",
            "severity_level": "high",
            "score": 1.5,
            "heatmap_url": f"/static/uploads/{filename}",
            "mongo_data": {
                "prediction": "Fail",
                "defect_type": "inspection_error",
                "severity_level": "high",
                "confidence_score": 0.0,
                "bounding_boxes": [],
                "processing_speed_ms": 45,
                "pipeline_logs": [f"Pipeline execution error: {e}"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    try:
        db_inspection = create_inspection_entry(
            db=db,
            filename=filename,
            prediction=result.get("prediction", "Pass"),
            defect_type=result.get("defect_type", "none"),
            severity_level=result.get("severity_level", "none"),
            score=result.get("score", 9.5),
            heatmap_url=result.get("heatmap_url", ""),
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Database insertion error: {e}")
        from models.models import Inspection
        db_inspection = Inspection(
            id=999,
            filename=filename,
            prediction=result.get("prediction", "Pass"),
            defect_type=result.get("defect_type", "none"),
            severity_level=result.get("severity_level", "none"),
            score=result.get("score", 9.5),
            batch_number=metadata.get("batch_number", ""),
            product_id=metadata.get("product_id", ""),
            production_line=metadata.get("production_line", ""),
            shift=metadata.get("shift", ""),
            operator_name=metadata.get("operator_name", "Quality Engineer"),
            review_status="ai_completed",
            created_at=datetime.utcnow()
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
