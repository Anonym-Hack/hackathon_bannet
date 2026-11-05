import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from app.schemas import AIAnalysisResult, AnalyzeTextRequest
from app.ai_service import analyze_material, rule_based_analyze
from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/ai", tags=["AI Analysis Engine"])

@router.post("/analyze-text", response_model=AIAnalysisResult)
async def analyze_text(payload: AnalyzeTextRequest):
    if not payload.description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description is required for AI material analysis."
        )
    return await analyze_material(
        title=payload.title or "",
        description=payload.description
    )

@router.post("/analyze-upload", response_model=AIAnalysisResult)
async def analyze_upload(
    title: Optional[str] = Form(""),
    description: Optional[str] = Form(""),
    category: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    temp_path = None
    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        content = await image.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file exceeds 5 MB limit."
            )
        temp_filename = f"temp_{uuid.uuid4().hex}{ext}"
        temp_path = UPLOAD_DIR / temp_filename
        with open(temp_path, "wb") as f:
            f.write(content)

    try:
        result = await analyze_material(
            title=title or "",
            description=description or "Industrial material sample from image upload",
            image_path=temp_path,
            category_hint=category
        )
        return result
    finally:
        # Clean up temporary upload if it was just for analysis
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
