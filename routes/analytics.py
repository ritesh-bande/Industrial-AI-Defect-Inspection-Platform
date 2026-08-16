import csv
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database.postgres import get_db
from models.models import User, Inspection
from authentication.jwt import get_current_user
from services.metrics_service import get_performance_metrics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
def get_analytics_summary_endpoint(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    production_line: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns quick quality summary KPIs: total count, pass/fail volumes, defect type spread, severity count.
    Used by the main dashboard.
    """
    # 1. Base query
    query = db.query(Inspection)
    if production_line:
        query = query.filter(Inspection.production_line == production_line)
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
        
    total = query.count()
    passed = query.filter(Inspection.prediction == "Pass").count()
    failed = query.filter(Inspection.prediction == "Fail").count()
    
    defect_types = {}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "none": 0}
    production_line_distribution = {}
    defect_type_by_line = {}
    trend_by_day = []
    
    inspections = query.all()
    for item in inspections:
        defect_types[item.defect_type] = defect_types.get(item.defect_type, 0) + 1
        severity_counts[item.severity_level] = severity_counts.get(item.severity_level, 0) + 1
        production_line_distribution[item.production_line] = production_line_distribution.get(item.production_line, 0) + 1
        
        # Line specific mapping
        line = item.production_line or "unassigned"
        if line not in defect_type_by_line:
            defect_type_by_line[line] = {}
        defect_type_by_line[line][item.defect_type] = defect_type_by_line[line].get(item.defect_type, 0) + 1
        
    # Generate daily trend for charts (group by created date)
    # Gather dates in sorted order
    dates_grouped = {}
    for item in inspections:
        day_str = item.created_at.strftime("%Y-%m-%d")
        if day_str not in dates_grouped:
            dates_grouped[day_str] = {"total": 0, "passed": 0, "failed": 0, "review": 0}
        dates_grouped[day_str]["total"] += 1
        if item.prediction == "Pass":
            dates_grouped[day_str]["passed"] += 1
        else:
            dates_grouped[day_str]["failed"] += 1
        if item.review_status == "manual_review":
            dates_grouped[day_str]["review"] += 1
            
    for k in sorted(dates_grouped.keys()):
        stats = dates_grouped[k]
        tot = stats["total"]
        trend_by_day.append({
            "date": k,
            "pass_rate": round(stats["passed"] / tot, 3) if tot > 0 else 1.0,
            "defect_rate": round(stats["failed"] / tot, 3) if tot > 0 else 0.0,
            "review": stats["review"],
            "total": tot
        })
        
    # Fallback default values if empty
    if not trend_by_day:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        trend_by_day = [{"date": today, "pass_rate": 1.0, "defect_rate": 0.0, "review": 0, "total": 0}]

    return {
        "total_inspections": total,
        "pass_count": passed,
        "fail_count": failed,
        "defect_rate": round((failed / total), 4) if total > 0 else 0.0,
        "yield_rate": round((passed / total * 100), 2) if total > 0 else 100.0,
        "defect_type_distribution": defect_types,
        "severity_distribution": severity_counts,
        "production_line_distribution": production_line_distribution,
        "defect_type_by_line": defect_type_by_line,
        "trend_by_day": trend_by_day,
        "average_confidence": 0.912 if total == 0 else round(sum([i.score for i in inspections if i.score > 0]) / (total * 10.0), 3)
    }

@router.get("")
def get_compiled_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns full AI model, manufacturing, and hardware metrics.
    Used by the Analytics Dashboard.
    """
    return get_performance_metrics(db)

@router.get("/export.csv")
def export_analytics_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates and downloads a CSV export containing all historical inspections.
    """
    inspections = db.query(Inspection).order_by(Inspection.created_at.desc()).all()
    
    # Setup CSV output stream
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Inspection ID", "Filename", "Prediction", "Defect Type", 
        "Severity", "Anomaly Score", "Production Line", "Batch Number", 
        "Product ID", "Shift", "Operator", "Review Status", "Created At"
    ])
    
    # Rows
    for item in inspections:
        writer.writerow([
            item.id, item.filename, item.prediction, item.defect_type,
            item.severity_level, item.score, item.production_line, item.batch_number,
            item.product_id, item.shift, item.operator_name, item.review_status,
            item.created_at.isoformat()
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=visioninspect_inspections.csv"}
    )
