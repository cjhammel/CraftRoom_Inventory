import os
import logging
import shutil
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form, Request

# Load .env file
_env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
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
from app.schemas import (
    AIAnalysisRequest,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    StampCreate,
    StampResponse,
    StampUpdate,
)
from app.crud import (
    create_location,
    create_stamp,
    delete_stamp,
    get_location,
    get_locations,
    get_stamp,
    get_stamps,
    update_location,
    update_stamp,
)
from app.image_utils import validate_image_file, generate_safe_filename, resize_image, UPLOAD_DIR

app = FastAPI(title="CraftRoom Product Inventory")

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


def _parse_location_id(location_id: Optional[str]) -> Optional[int]:
    if location_id is None or not str(location_id).strip():
        return None
    try:
        return int(location_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="location_id must be an integer")


@app.on_event("startup")
def startup():
    logger.info("Starting CraftRoom Product Inventory backend")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'using default')}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"AI API URL: {os.getenv('AI_API_URL', 'using default')}")
    init_db()
    logger.info("Database initialized successfully")


# --- Stamp CRUD endpoints ---


@app.get("/locations", response_model=list[LocationResponse])
def list_locations(db: Session = Depends(get_db)):
    try:
        return get_locations(db)
    except Exception as e:
        logger.error(f"Error listing locations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list locations")


@app.post("/locations", response_model=LocationResponse)
def create_location_endpoint(location: LocationCreate, db: Session = Depends(get_db)):
    try:
        return create_location(db, location.model_dump())
    except Exception as e:
        logger.error(f"Error creating location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create location")


@app.put("/locations/{location_id}", response_model=LocationResponse)
def update_location_endpoint(
    location_id: int,
    location: LocationUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated = update_location(db, location_id, location.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Location not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location {location_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update location")


@app.get("/stamps", response_model=list[StampResponse])
def list_stamps(
    q: Optional[str] = Query(None),
    brand_name: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    sentiments: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        stamps = get_stamps(
            db,
            search=q,
            brand_name=brand_name,
            product_type=product_type,
            theme=theme,
            location=location,
            sentiments=sentiments,
        )
        logger.info(f"Listed {len(stamps)} stamps (q={q}, brand={brand_name}, product_type={product_type}, theme={theme}, loc={location}, sentiments={sentiments})")
        return stamps
    except HTTPException:
        raise
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
    product_name: Optional[str] = Form(None),
    item_number: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    product_type: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    shape_descriptor: Optional[str] = Form(None),
    sentiments: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    cabinet: Optional[str] = Form(None),
    shelf: Optional[str] = Form(None),
    bin: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    logger.info(f"Creating stamp: {product_name}")
    
    # Validate product_name
    if not product_name or not product_name.strip():
        logger.warning(f"Empty product_name received")
        raise HTTPException(status_code=400, detail="product_name is required and cannot be empty")

    stamp_data = {
        "product_name": product_name.strip(),
        "item_number": item_number,
        "brand_name": brand_name,
        "product_type": product_type,
        "theme": theme,
        "shape_descriptor": shape_descriptor,
        "sentiments": sentiments,
    }
    parsed_location_id = _parse_location_id(location_id)
    if parsed_location_id is not None:
        if not get_location(db, parsed_location_id):
            raise HTTPException(status_code=400, detail="location_id does not exist")
        stamp_data["location_id"] = parsed_location_id
    else:
        location_parts = {"cabinet": cabinet, "shelf": shelf, "bin": bin}
        if any(value is not None for value in location_parts.values()):
            stamp_data["location"] = location_parts
        elif location is not None:
            stamp_data["location"] = location

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
    request: Request,
    stamp_id: int,
    product_name: Optional[str] = Form(None),
    item_number: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    product_type: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    shape_descriptor: Optional[str] = Form(None),
    sentiments: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    cabinet: Optional[str] = Form(None),
    shelf: Optional[str] = Form(None),
    bin: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    logger.info(f"Updating stamp: {stamp_id}")
    stamp = get_stamp(db, stamp_id)
    if not stamp:
        logger.warning(f"Stamp not found for update: {stamp_id}")
        raise HTTPException(status_code=404, detail="Stamp not found")

    form = await request.form()
    stamp_data = {}
    if "product_name" in form and not str(form.get("product_name") or "").strip():
        logger.warning(f"Empty product_name received for stamp {stamp_id}")
        raise HTTPException(status_code=400, detail="product_name is required and cannot be empty")
    if product_name is not None:
        if not product_name.strip():
            logger.warning(f"Empty product_name received for stamp {stamp_id}")
            raise HTTPException(status_code=400, detail="product_name is required and cannot be empty")
        stamp_data["product_name"] = product_name.strip()
    if item_number is not None:
        stamp_data["item_number"] = item_number
    if brand_name is not None:
        stamp_data["brand_name"] = brand_name
    if product_type is not None:
        stamp_data["product_type"] = product_type
    if theme is not None:
        stamp_data["theme"] = theme
    if shape_descriptor is not None:
        stamp_data["shape_descriptor"] = shape_descriptor
    if sentiments is not None:
        stamp_data["sentiments"] = sentiments
    if location_id is not None:
        parsed_location_id = _parse_location_id(location_id)
        if parsed_location_id is not None and not get_location(db, parsed_location_id):
            raise HTTPException(status_code=400, detail="location_id does not exist")
        stamp_data["location_id"] = parsed_location_id
    else:
        location_parts = {"cabinet": cabinet, "shelf": shelf, "bin": bin}
        if any(value is not None for value in location_parts.values()):
            stamp_data["location"] = location_parts
        elif location is not None:
            stamp_data["location"] = location

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
    ai_api_url: Optional[str] = Form(None),
    ai_prompt: Optional[str] = Form(None),
):
    logger.info(f"AI image analysis requested: {image.filename}")
    request_ai_api_url = ai_api_url.strip() if ai_api_url else ""
    effective_ai_api_url = request_ai_api_url or (os.getenv("AI_API_URL") or "").strip()
    effective_ai_prompt = (ai_prompt or os.getenv("AI_PROMPT") or "").strip() or None
    if not effective_ai_api_url:
        logger.warning("AI analysis requested but AI_API_URL not configured")
        raise HTTPException(
            status_code=501,
            detail={
                "message": "AI service is not configured. Set AI_API_URL in your .env file or the app configuration menu to enable image analysis.",
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

    ai_api_key = "" if request_ai_api_url else os.getenv("AI_API_KEY", "")

    # Save temporarily for AI processing
    temp_path = os.path.join(UPLOAD_DIR, f"temp_ai_{generate_safe_filename(image.filename)}")
    contents = await image.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        logger.info(f"Calling AI API with model: {os.getenv('AI_MODEL')}")
        suggestions = await call_ai_api(temp_path, ai_api_key, effective_ai_api_url, effective_ai_prompt)
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


async def call_ai_api(
    image_path: str,
    api_key: str,
    ai_api_url: Optional[str] = None,
    ai_prompt: Optional[str] = None,
) -> dict:
    """Call Ollama or llama.cpp-compatible API to analyze stamp image.

    Supports both Ollama /api/chat and OpenAI-compatible /v1/chat/completions
    endpoints. Auto-detects based on AI_API_URL path or AI_API_KEY presence.
    """
    import httpx

    ai_api_url = ai_api_url or os.getenv("AI_API_URL", "http://example.com:11434")
    ai_model = os.getenv("AI_MODEL", "qwen3.6:35B")
    ai_prompt = ai_prompt or os.getenv("AI_PROMPT", "Analyze this stamp image and return a JSON object with these exact keys: product_name, brand_name, product_type, theme, shape_descriptor, sentiments. Use null for unknown fields. Example: {\"product_name\": \"Test\", \"brand_name\": null, \"product_type\": null, \"theme\": null, \"shape_descriptor\": null, \"sentiments\": null}. Return ONLY valid JSON, no markdown, no explanation.")

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

    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                if result.get("choices", [{}])[0].get("message", {}).get("content"):
                    break
                if attempt < max_retries - 1:
                    logger.warning(f"AI returned empty content on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling AI API (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            raise
        except Exception as e:
            logger.error(f"Error calling AI API (attempt {attempt + 1}): {e}", exc_info=True)
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            raise

    # Parse AI response and extract suggestions
    if is_openai_compat:
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        finish_reason = result.get("choices", [{}])[0].get("finish_reason", "unknown")
    else:
        content = result.get("message", {}).get("content", "")
        finish_reason = result.get("done", False)
    
    logger.debug(f"AI raw response content length: {len(content)}, finish_reason: {finish_reason}")
    logger.debug(f"AI full response: {result}")
    
    if not content:
        logger.warning("AI API returned empty content")
        return {}

    import json
    try:
        suggestions = json.loads(content)
        logger.info(f"AI analysis successful: extracted {len(suggestions)} fields")
    except json.JSONDecodeError as e:
        logger.warning(f"AI API returned non-JSON content, attempting to extract from markdown. Error: {e}")
        logger.debug(f"AI content that failed to parse: {content[:500]}")
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
