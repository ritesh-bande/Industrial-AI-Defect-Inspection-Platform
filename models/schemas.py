from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "operator"

class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# --- INSPECTION SCHEMAS ---
class InspectionCreate(BaseModel):
    batch_number: Optional[str] = ""
    product_id: Optional[str] = ""
    production_line: Optional[str] = ""
    shift: Optional[str] = ""
    operator_name: Optional[str] = ""

class InspectionUpdate(BaseModel):
    review_status: str
    review_notes: Optional[str] = ""

class InspectionMetadataUpdate(BaseModel):
    batch_number: Optional[str] = None
    product_id: Optional[str] = None
    production_line: Optional[str] = None
    shift: Optional[str] = None
    operator_name: Optional[str] = None

class InspectionResponse(BaseModel):
    id: int
    filename: str
    prediction: str
    defect_type: str
    severity_level: str
    score: float
    heatmap_url: Optional[str] = None
    batch_number: str
    product_id: str
    production_line: str
    shift: str
    operator_name: str
    review_status: str
    review_notes: str
    created_at: datetime
    mongo_metadata_id: Optional[str] = None
    image_url: str

    class Config:
        from_attributes = True

# --- REWORK TICKET SCHEMAS ---
class ReworkTicketCreate(BaseModel):
    inspection_id: int
    notes: Optional[str] = ""
    priority: Optional[str] = "Medium"

class ReworkTicketUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None

class ReworkTicketResponse(BaseModel):
    id: int
    inspection_id: int
    ticket_number: str
    status: str
    notes: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- PRODUCTION LINE SCHEMAS ---
class ProductionLineCreate(BaseModel):
    name: str
    code: str
    status: Optional[bool] = True
    description: Optional[str] = None

class ProductionLineResponse(BaseModel):
    id: int
    name: str
    code: str
    status: bool
    description: Optional[str]

    class Config:
        from_attributes = True

# --- ANALYTICS SCHEMAS ---
class AnalyticsSummary(BaseModel):
    total_inspections: int
    passed: int
    failed: int
    yield_rate: float

class AnalyticsMetricEntry(BaseModel):
    timestamp: datetime
    metric_type: str
    metric_name: str
    metric_value: float
    product_id: Optional[str]
    production_line: Optional[str]
