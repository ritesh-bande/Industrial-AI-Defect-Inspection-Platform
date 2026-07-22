from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.postgres import get_db
from models.models import User, ProductionLine
from models.schemas import ProductionLineResponse, ProductionLineCreate
from authentication.jwt import get_current_user
from authentication.roles import require_supervisor, require_admin
from services.db_service import list_production_lines, create_production_line_entry

router = APIRouter(prefix="/api/production", tags=["Production & Catalog"])

@router.get("/catalog")
def get_catalog_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns standard metadata catalogs for selection dropdowns (products and production lines).
    """
    lines = list_production_lines(db)
    
    # Standard product catalog
    products = [
        {"product_id": "bottle", "name": "MVTec Bottle"},
        {"product_id": "cable", "name": "MVTec Cable"},
        {"product_id": "carpet", "name": "MVTec Carpet"},
        {"product_id": "leather", "name": "MVTec Leather"},
        {"product_id": "tile", "name": "MVTec Tile"},
        {"product_id": "wood", "name": "MVTec Wood"}
    ]
    
    # If no lines exist, seed default lines
    if not lines:
        default_lines = [
            {"name": "Assembly Line Alpha", "code": "line_1", "description": "Primary assembly line"},
            {"name": "Inspection Conveyor Beta", "code": "line_2", "description": "Defect scanning station"},
            {"name": "Packaging Line Gamma", "code": "line_3", "description": "End-of-line packaging line"}
        ]
        seeded_lines = []
        for l in default_lines:
            line_obj = ProductionLine(name=l["name"], code=l["code"], description=l["description"], status=True)
            db.add(line_obj)
            seeded_lines.append(line_obj)
        db.commit()
        lines = seeded_lines
        
    return {
        "products": products,
        "production_lines": [{"line_id": l.code, "name": l.name} for l in lines]
    }

@router.get("/lines", response_model=List[ProductionLineResponse])
def get_production_lines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all active production lines.
    """
    return list_production_lines(db)

@router.post("/lines", response_model=ProductionLineResponse, status_code=status.HTTP_201_CREATED)
def create_production_line(
    payload: ProductionLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
):
    """
    Register a new production line.
    """
    # Check duplicate code
    existing = db.query(ProductionLine).filter(ProductionLine.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Production line with this code already exists."
        )
    return create_production_line_entry(db, payload)
