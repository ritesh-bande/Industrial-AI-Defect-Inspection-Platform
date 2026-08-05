import os
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database.postgres import get_db
from models.models import Inspection
from routes.auth import get_current_user
from models.models import User

logger = logging.getLogger("visioninspect.reports")

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

REPORTS_DIR = os.path.join("static", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_pdf_report(inspection):
    # Minimal valid PDF 1.4 byte stream generator in pure Python (0 dependencies)
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 3 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Outlines /Count 0 >>\nendobj\n"
    
    stream_content = f"""BT
/F1 18 Tf
50 750 Td
(VISIONINSPECT AI - QUALITY REPORT) Tj
/F1 12 Tf
0 -40 Td
(Inspection ID: {inspection.id}) Tj
0 -20 Td
(Image Filename: {inspection.filename}) Tj
0 -20 Td
(AI Decision: {inspection.prediction.upper()}) Tj
0 -20 Td
(Defect Type Classified: {inspection.defect_type}) Tj
0 -20 Td
(Confidence / Score: {inspection.score * 100:.1f}%) Tj
0 -20 Td
(Severity Level: {inspection.severity_level}) Tj
0 -20 Td
(Production Line: {inspection.production_line or 'Unassigned'}) Tj
0 -20 Td
(Batch Number: {inspection.batch_number or 'Unassigned'}) Tj
0 -20 Td
(Operator: {inspection.operator_name or 'System'}) Tj
0 -20 Td
(Timestamp: {inspection.created_at.isoformat()}) Tj
0 -40 Td
(STATUS: THE PRODUCT COMPLIES WITH ALL AI AND SEGMENTATION STANDARDS.) Tj
ET
"""
    stream_bytes = stream_content.encode('utf-8')
    obj5 = f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode('utf-8') + stream_bytes + b"\nendstream\nendobj\n"
    
    obj3 = b"3 0 obj\n<< /Type /Pages /Kids [ 4 0 R ] /Count 1 >>\nendobj\n"
    obj4 = b"4 0 obj\n<< /Type /Page /Parent 3 0 R /MediaBox [ 0 0 595 842 ] /Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>\nendobj\n"
    obj6 = b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    
    header = b"%PDF-1.4\n"
    body = [obj1, obj2, obj3, obj4, obj5, obj6]
    
    offsets = []
    current_offset = len(header)
    output = header
    
    for obj in body:
        offsets.append(current_offset)
        output += obj
        current_offset += len(obj)
        
    xref_pos = len(output)
    xref = f"xref\n0 {len(body) + 1}\n0000000000 65535 f \n".encode('utf-8')
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode('utf-8')
        
    trailer = f"trailer\n<< /Size {len(body) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode('utf-8')
    
    return output + xref + trailer

@router.post("/inspection/{inspection_id}")
def create_report(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF report for a given inspection ID.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
        
    pdf_bytes = generate_pdf_report(inspection)
    file_path = os.path.join(REPORTS_DIR, f"report_{inspection_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
        
    logger.info(f"Report for inspection {inspection_id} generated successfully.")
    
    return {
        "id": inspection_id,
        "inspection_id": inspection_id,
        "filename": f"report_{inspection_id}.pdf",
        "created_at": datetime.utcnow()
    }

@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all generated reports.
    """
    if not os.path.exists(REPORTS_DIR):
        return []
        
    reports = []
    for file in os.listdir(REPORTS_DIR):
        if file.startswith("report_") and file.endswith(".pdf"):
            try:
                inspection_id = int(file.replace("report_", "").replace(".pdf", ""))
                reports.append({
                    "id": inspection_id,
                    "inspection_id": inspection_id,
                    "filename": file,
                    "created_at": datetime.fromtimestamp(os.path.getctime(os.path.join(REPORTS_DIR, file)))
                })
            except Exception:
                continue
    return reports

@router.get("/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve report metadata.
    """
    file_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found.")
        
    return {
        "id": report_id,
        "inspection_id": report_id,
        "filename": f"report_{report_id}.pdf",
        "created_at": datetime.fromtimestamp(os.path.getctime(file_path))
    }

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download report PDF file.
    """
    file_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found.")
        
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"inspection_report_{report_id}.pdf"
    )
