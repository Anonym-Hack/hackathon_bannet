from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- AUTH SCHEMAS ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    company_name: str = Field(..., min_length=2)
    role: str = Field("Supplier", pattern="^(Supplier|Buyer)$")
    city: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    email: str
    company_name: str
    role: str
    city: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI ANALYSIS SCHEMAS ---

class AIAnalysisResult(BaseModel):
    material_name: str
    category: str
    composition: str
    condition: str
    reuse_applications: List[str]
    target_industries: List[str]
    handling_notes: str
    sustainability_score: int = Field(ge=0, le=100)
    confidence: str = "High"  # High, Medium, Low
    is_hazardous: bool = False
    safety_warning: Optional[str] = None
    is_demo_mode: bool = True

class AnalyzeTextRequest(BaseModel):
    title: Optional[str] = ""
    description: str

# --- LISTING SCHEMAS ---

class ListingBase(BaseModel):
    title: str = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
    category: str
    quantity: float = Field(..., gt=0)
    unit: str = "kg"
    price_type: str = "fixed"  # fixed, free, negotiable
    price: float = Field(default=0.0, ge=0)
    location: str
    availability_status: str = "available"

class ListingCreate(ListingBase):
    image_url: Optional[str] = None
    # Optional pre-computed AI analysis fields
    ai_material_name: Optional[str] = None
    ai_composition: Optional[str] = None
    ai_condition: Optional[str] = None
    ai_reuse_applications: Optional[List[str]] = None
    ai_target_industries: Optional[List[str]] = None
    ai_handling_notes: Optional[str] = None
    ai_sustainability_score: Optional[int] = 75
    ai_confidence: Optional[str] = "High"
    ai_is_demo_mode: Optional[bool] = True
    is_hazardous: Optional[bool] = False

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_type: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    availability_status: Optional[str] = None
    image_url: Optional[str] = None
    is_hazardous: Optional[bool] = None

class ListingResponse(ListingBase):
    id: int
    supplier_id: int
    image_url: Optional[str] = None
    ai_material_name: Optional[str] = None
    ai_composition: Optional[str] = None
    ai_condition: Optional[str] = None
    ai_reuse_applications: List[str] = []
    ai_target_industries: List[str] = []
    ai_handling_notes: Optional[str] = None
    ai_sustainability_score: int = 70
    ai_confidence: str = "High"
    ai_is_demo_mode: bool = True
    is_hazardous: bool = False
    created_at: datetime
    updated_at: datetime
    supplier: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- BUYER REQUEST SCHEMAS ---

class BuyerRequestBase(BaseModel):
    material_name: str = Field(..., min_length=2)
    category: str
    quantity_needed: float = Field(..., gt=0)
    unit: str = "kg"
    location: str
    use_case: Optional[str] = None

class BuyerRequestCreate(BuyerRequestBase):
    pass

class BuyerRequestUpdate(BaseModel):
    material_name: Optional[str] = None
    category: Optional[str] = None
    quantity_needed: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    use_case: Optional[str] = None
    status: Optional[str] = None

class BuyerRequestResponse(BuyerRequestBase):
    id: int
    buyer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    buyer: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- MATCH SCHEMAS ---

class MatchResult(BaseModel):
    match_score: int  # 0 to 100
    why_matched: List[str]
    listing: Optional[ListingResponse] = None
    request: Optional[BuyerRequestResponse] = None

# --- INQUIRY & CHAT SCHEMAS ---

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    id: int
    inquiry_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime
    sender_company: Optional[str] = None
    sender_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class InquiryCreate(BaseModel):
    listing_id: int
    subject: str = Field(..., min_length=2)
    message: str = Field(..., min_length=2)

class InquiryResponse(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    supplier_id: int
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    listing_title: Optional[str] = None
    buyer_company: Optional[str] = None
    supplier_company: Optional[str] = None
    unread_count: int = 0
    latest_message: Optional[str] = None
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- IMPACT ANALYTICS SCHEMAS ---

class CategoryImpact(BaseModel):
    category: str
    weight_kg: float
    co2_saved_kg: float
    listings_count: int

class ImpactStatsResponse(BaseModel):
    total_waste_diverted_kg: float
    estimated_co2_saved_kg: float
    estimated_cost_savings_usd: float
    active_listings_count: int
    active_requests_count: int
    registered_companies_count: int
    category_breakdown: List[CategoryImpact]
    disclaimer: str = "All values are realistic circular-economy estimations based on material composition and lifecycle emissions models."
