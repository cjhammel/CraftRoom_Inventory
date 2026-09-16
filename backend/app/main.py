import os
import logging
import shutil
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form

# Load .env file
_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("craftroom")

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
    logger.info("Starting CraftRoom Stamp Inventory backend")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'using default')}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"AI API URL: {os.getenv('AI_API_URL', 'using default')}")
    init_db()
    logger.info("Database initialized successfully")


# --- Stamp CRUD endpoints ---


@app.get("/stamps", response_model=list[StampResponse])
def list_stamps(
    q: Optional[str] = Query(None),
    brand_name: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    sentiments: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        stamps = get_stamps(db, search=q, brand_name=brand_name, product_type=product_type, location=location, sentiments=sentiments)
        logger.info(f"Listed {len(stamps)} stamps (q={q}, brand={brand_name}, type={product_type}, loc={location}, sentiments={sentiments})")
        return stamps
    except Exception as e:
        logger.error(f"Error listing stamps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list stamps")


@app.get("/stamps/{stamp_id}", response_model=StampResponse)
def get_stamp_by_id(stamp_id: int, db: Session = Depends(get_db)):
    try:
        stamp = get_stamp(db, stamp_id)
        if not stamp:
            logger.warning(f"Stamp not found: {stamp_id}")
            raise HTTPException(status_code=404, detail="Stamp not found")
        logger.info(f"Retrieved stamp: {stamp_id}")
        return stamp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stamp {stamp_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve stamp")


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
    logger.info(f"Creating stamp: {product_name}")
    
    # Validate product_name
    if not product_name or not product_name.strip():
        logger.warning(f"Empty product_name received")
        raise HTTPException(status_code=400, detail="product_name is required and cannot be empty")

    # Validate price
    if price is not None:
        try:
            float(price)
        except ValueError:
            logger.warning(f"Invalid price format: {price}")
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
        logger.info(f"Processing image upload: {image.filename}")
        bad_ext = validate_image_file(image)
        if bad_ext:
            logger.warning(f"Unsupported image type: {bad_ext} for file {image.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
            )

        safe_filename = generate_safe_filename(image.filename)
        input_path = os.path.join(UPLOAD_DIR, f"temp_{safe_filename}")
        output_path = os.path.join(UPLOAD_DIR, safe_filename)

        try:
            # Save uploaded file
            contents = await image.read()
            with open(input_path, "wb") as f:
                f.write(contents)

            # Resize/compress with ffmpeg
            resize_image(input_path, output_path)
            os.remove(input_path)

            stamp_data["image_url"] = f"/uploads/{safe_filename}"
            logger.info(f"Image processed and saved: {safe_filename}")
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            if os.path.exists(input_path):
                os.remove(input_path)
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    try:
        db_stamp = create_stamp(db, stamp_data)
        logger.info(f"Stamp created successfully with ID: {db_stamp.id}")
        return StampResponse.model_validate(db_stamp)
    except Exception as e:
        logger.error(f"Error creating stamp in database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create stamp in database")


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
    logger.info(f"Updating stamp: {stamp_id}")
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        logger.warning(f"Stamp not found for update: {stamp_id}")
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
        logger.info(f"Processing image upload for stamp {stamp_id}: {image.filename}")
        bad_ext = validate_image_file(image)
        if bad_ext:
            logger.warning(f"Unsupported image type: {bad_ext} for stamp {stamp_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
            )

        safe_filename = generate_safe_filename(image.filename)
        input_path = os.path.join(UPLOAD_DIR, f"temp_{safe_filename}")
        output_path = os.path.join(UPLOAD_DIR, safe_filename)

        try:
            contents = await image.read()
            with open(input_path, "wb") as f:
                f.write(contents)

            resize_image(input_path, output_path)
            os.remove(input_path)

            stamp_data["image_url"] = f"/uploads/{safe_filename}"
            logger.info(f"Image updated for stamp {stamp_id}: {safe_filename}")
        except Exception as e:
            logger.error(f"Error processing image for stamp {stamp_id}: {e}", exc_info=True)
            if os.path.exists(input_path):
                os.remove(input_path)
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    try:
        updated = update_stamp(db, stamp_id, stamp_data)
        logger.info(f"Stamp {stamp_id} updated successfully")
        return StampResponse.model_validate(updated)
    except Exception as e:
        logger.error(f"Error updating stamp {stamp_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update stamp in database")


@app.delete("/stamps/{stamp_id}")
def delete_stamp_endpoint(stamp_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting stamp: {stamp_id}")
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        logger.warning(f"Stamp not found for deletion: {stamp_id}")
        raise HTTPException(status_code=404, detail="Stamp not found")

    # Remove image file if it exists
    if stamp.image_url:
        filename = os.path.basename(stamp.image_url)
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted image file: {filename}")
            except Exception as e:
                logger.error(f"Error deleting image file {filename}: {e}")

    try:
        delete_stamp(db, stamp_id)
        logger.info(f"Stamp {stamp_id} deleted successfully")
        return {"detail": "Stamp deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting stamp {stamp_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete stamp from database")


# --- AI endpoints ---


@app.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
):
    logger.info(f"AI image analysis requested: {image.filename}")
    ai_api_url = os.getenv("AI_API_URL")
    if not ai_api_url:
        logger.warning("AI analysis requested but AI_API_URL not configured")
        raise HTTPException(
            status_code=501,
            detail={
                "message": "AI service is not configured. Set AI_API_URL in your .env file to enable image analysis.",
                "suggestions": {},
            },
        )

    bad_ext = validate_image_file(image)
    if bad_ext:
        logger.warning(f"Unsupported image type for AI analysis: {bad_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: .{bad_ext.lstrip('.')}. Supported: jpg, jpeg, png, webp",
        )

    ai_api_key = os.getenv("AI_API_KEY", "")

    # Save temporarily for AI processing
    temp_path = os.path.join(UPLOAD_DIR, f"temp_ai_{generate_safe_filename(image.filename)}")
    contents = await image.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        logger.info(f"Calling AI API with model: {os.getenv('AI_MODEL')}")
        suggestions = await call_ai_api(temp_path, ai_api_key)
        logger.info(f"AI analysis completed successfully")
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
        return {"suggestions": {}, "error": str(e)}
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp AI file: {e}")


async def call_ai_api(image_path: str, api_key: str) -> dict:
    """Call Ollama or llama.cpp-compatible API to analyze stamp image.

    Supports both Ollama /api/chat and OpenAI-compatible /v1/chat/completions
    endpoints. Auto-detects based on AI_API_URL path or AI_API_KEY presence.
    """
    import httpx

    ai_api_url = os.getenv("AI_API_URL", "http://example.com:11434")
    ai_model = os.getenv("AI_MODEL", "qwen3.6:35B")
    ai_prompt = os.getenv("AI_PROMPT", "Analyze this stamp image and return product_name, brand_name, product_type, theme, shape_descriptor, sentiments as JSON.")

    logger.info(f"Calling AI API: {ai_api_url} with model {ai_model}")

    # Read image and encode as base64
    import base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine MIME type
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    # Auto-detect API type: OpenAI-compatible if URL contains /v1 or API key is set
    # Strip trailing /v1 to avoid duplicate path segments
    base_url = ai_api_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    is_openai_compat = "/v1" in ai_api_url or bool(api_key)

    if is_openai_compat:
        # OpenAI-compatible endpoint (llama.cpp, vLLM, etc.)
        endpoint_url = f"{base_url}/v1/chat/completions"
        payload = {
            "model": ai_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ai_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    ],
                }
            ],
            "max_tokens": 1000,
            "temperature": 0,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    else:
        # Ollama /api/chat endpoint
        endpoint_url = f"{ai_api_url.rstrip('/')}/api/chat"
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
        headers = {}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                endpoint_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling AI API: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calling AI API: {e}", exc_info=True)
        raise

    # Parse AI response and extract suggestions
    if is_openai_compat:
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        content = result.get("message", {}).get("content", "")
    if not content:
        logger.warning("AI API returned empty content")
        logger.debug("Full AI response: %s", result)
        return {}

    import json
    try:
        suggestions = json.loads(content)
        logger.info(f"AI analysis successful: extracted {len(suggestions)} fields")
    except json.JSONDecodeError:
        logger.warning("AI API returned non-JSON content, attempting to extract from markdown")
        # Try to extract JSON from markdown code blocks
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                suggestions = json.loads(match.group(1))
                logger.info(f"AI analysis successful (markdown): extracted {len(suggestions)} fields")
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from markdown code block")
                suggestions = {}
        else:
            logger.error("Could not extract JSON from AI response")
            suggestions = {}

    return suggestions


# Serve uploaded images via static mount — already handled by app.mount above
