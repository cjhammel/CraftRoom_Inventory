import os
import shutil
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import Stamp
from app.schemas import StampCreate, StampUpdate, StampResponse, AIAnalysisRequest
from app.crud import get_stamp, get_stamps, create_stamp, update_stamp, delete_stamp
from app.image_utils import validate_image_file, generate_safe_filename, resize_image, UPLOAD_DIR

app = FastAPI(title="CraftRoom Stamp Inventory")

# CORS
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def startup():
    init_db()


# --- Stamp CRUD endpoints ---


@app.get("/stamps", response_model=list[StampResponse])
def list_stamps(
    q: Optional[str] = Query(None),
    brand_name: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    stamps = get_stamps(db, search=q, brand_name=brand_name, product_type=product_type, location=location)
    return stamps


@app.get("/stamps/{stamp_id}", response_model=StampResponse)
def get_stamp_by_id(stamp_id: int, db: Session = Depends(get_db)):
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        raise HTTPException(status_code=404, detail="Stamp not found")
    return stamp


@app.post("/stamps", response_model=StampResponse)
async def create_stamp_endpoint(
    product_name: str = Form(...),
    brand_name: Optional[str] = Form(None),
    retired: bool = Form(False),
    product_type: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    shape_descriptor: Optional[str] = Form(None),
    sentiments: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Validate product_name
    if not product_name or not product_name.strip():
        raise HTTPException(status_code=400, detail="product_name is required and cannot be empty")

    # Validate price
    if price is not None:
        try:
            float(price)
        except ValueError:
            raise HTTPException(status_code=400, detail="price must be a valid decimal number")

    stamp_data = {
        "product_name": product_name.strip(),
        "brand_name": brand_name,
        "retired": retired,
        "product_type": product_type,
        "theme": theme,
        "shape_descriptor": shape_descriptor,
        "sentiments": sentiments,
        "location": location,
        "price": price,
    }

    # Handle image upload
    if image and image.filename:
        bad_ext = validate_image_file(image)
        if bad_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
            )

        safe_filename = generate_safe_filename(image.filename)
        input_path = os.path.join(UPLOAD_DIR, f"temp_{safe_filename}")
        output_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Save uploaded file
        contents = await image.read()
        with open(input_path, "wb") as f:
            f.write(contents)

        # Resize/compress with ffmpeg
        resize_image(input_path, output_path)
        os.remove(input_path)

        stamp_data["image_url"] = f"/uploads/{safe_filename}"

    db_stamp = create_stamp(db, stamp_data)
    return StampResponse.model_validate(db_stamp)


@app.put("/stamps/{stamp_id}", response_model=StampResponse)
async def update_stamp_endpoint(
    stamp_id: int,
    product_name: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    retired: Optional[bool] = Form(None),
    product_type: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    shape_descriptor: Optional[str] = Form(None),
    sentiments: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        raise HTTPException(status_code=404, detail="Stamp not found")

    stamp_data = {}
    if product_name is not None:
        stamp_data["product_name"] = product_name.strip()
    if brand_name is not None:
        stamp_data["brand_name"] = brand_name
    if retired is not None:
        stamp_data["retired"] = retired
    if product_type is not None:
        stamp_data["product_type"] = product_type
    if theme is not None:
        stamp_data["theme"] = theme
    if shape_descriptor is not None:
        stamp_data["shape_descriptor"] = shape_descriptor
    if sentiments is not None:
        stamp_data["sentiments"] = sentiments
    if location is not None:
        stamp_data["location"] = location
    if price is not None:
        stamp_data["price"] = price

    # Handle image upload
    if image and image.filename:
        bad_ext = validate_image_file(image)
        if bad_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
            )

        safe_filename = generate_safe_filename(image.filename)
        input_path = os.path.join(UPLOAD_DIR, f"temp_{safe_filename}")
        output_path = os.path.join(UPLOAD_DIR, safe_filename)

        contents = await image.read()
        with open(input_path, "wb") as f:
            f.write(contents)

        resize_image(input_path, output_path)
        os.remove(input_path)

        stamp_data["image_url"] = f"/uploads/{safe_filename}"

    updated = update_stamp(db, stamp_id, stamp_data)
    return StampResponse.model_validate(updated)


@app.delete("/stamps/{stamp_id}")
def delete_stamp_endpoint(stamp_id: int, db: Session = Depends(get_db)):
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        raise HTTPException(status_code=404, detail="Stamp not found")

    # Remove image file if it exists
    if stamp.image_url:
        filename = os.path.basename(stamp.image_url)
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    delete_stamp(db, stamp_id)
    return {"detail": "Stamp deleted successfully"}


# --- AI endpoints ---


@app.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
):
    ai_api_key = os.getenv("AI_API_KEY")
    if not ai_api_key:
        raise HTTPException(
            status_code=501,
            detail={
                "message": "AI service is not configured. Set AI_API_KEY in your .env file to enable image analysis.",
                "suggestions": {},
            },
        )

    bad_ext = validate_image_file(image)
    if bad_ext:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
        )

    # Save temporarily for AI processing
    temp_path = os.path.join(UPLOAD_DIR, f"temp_ai_{generate_safe_filename(image.filename)}")
    contents = await image.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        # Call AI API (placeholder — implement based on your provider)
        suggestions = await call_ai_api(temp_path, ai_api_key)
        return {"suggestions": suggestions}
    except Exception as e:
        return {"suggestions": {}, "error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def call_ai_api(image_path: str, api_key: str) -> dict:
    """Call llama.cpp / Ollama-compatible API to analyze stamp image.

    Uses the Ollama /api/chat endpoint with multimodal support.
    Compatible with llama.cpp servers exposing Ollama-compatible API.
    """
    import httpx

    ai_api_url = os.getenv("AI_API_URL", "http://framework.gruru.net:11434")
    ai_model = os.getenv("AI_MODEL", "qwen3.6:35B")
    ai_prompt = os.getenv("AI_PROMPT", "Analyze this stamp image and return product_name, brand_name, product_type, theme, shape_descriptor, sentiments as JSON.")

    # Read image and encode as base64
    import base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine MIME type
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    # Ollama-compatible chat API payload
    payload = {
        "model": ai_model,
        "messages": [
            {
                "role": "user",
                "content": ai_prompt,
                "images": [image_data],
            }
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{ai_api_url.rstrip('/')}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    # Parse AI response and extract suggestions
    content = result.get("message", {}).get("content", "")
    if not content:
        return {}

    import json
    try:
        suggestions = json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            suggestions = json.loads(match.group(1))
        else:
            suggestions = {}

    return suggestions


# Serve uploaded images via static mount — already handled by app.mount above
