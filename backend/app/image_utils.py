import os
import uuid
import subprocess
import shutil
import logging
from pathlib import Path

from app.config import get_upload_dir

logger = logging.getLogger("craftroom")

UPLOAD_DIR = get_upload_dir()
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 1_000_000  # 1 MB target


def validate_image_file(file) -> str | None:
    """Validate uploaded image file type. Returns the extension or None if invalid."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return ext  # return the bad extension for the error message
    return None


def generate_safe_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def resize_image(input_path: str, output_path: str) -> str:
    """Reduce image file size if larger than MAX_FILE_SIZE using quality compression (-q:v 4)."""
    input_size = os.path.getsize(input_path)
    input_size_mb = input_size / 1_000_000

    if input_size <= MAX_FILE_SIZE:
        logger.info(f"Image {os.path.basename(input_path)}: {input_size_mb:.2f} MB, under 1MB threshold — copying as-is")
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        return output_path

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        # In-place resize: write to temp file then replace
        # Use .resized before extension so ffmpeg can detect output format
        base, ext = os.path.splitext(output_path)
        tmp_path = f"{base}.resized{ext}"
    else:
        tmp_path = output_path

    try:
        cmd = [
            "ffmpeg", "-i", input_path,
            "-q:v", "4",
            "-y",
            tmp_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()[:200]}")

    except FileNotFoundError:
        logger.warning("ffmpeg/ffprobe not found, copying file without resize")
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        else:
            shutil.copy2(input_path, tmp_path)
    except Exception as e:
        logger.error(f"Error during image resize: {e}", exc_info=True)
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        else:
            shutil.copy2(input_path, tmp_path)

    if tmp_path != output_path and os.path.exists(tmp_path):
        os.replace(tmp_path, output_path)

    output_size = os.path.getsize(output_path)
    output_size_mb = output_size / 1_000_000
    reduction = ((input_size - output_size) / input_size) * 100
    logger.info(f"Image {os.path.basename(input_path)}: compressed q:v 4 — {input_size_mb:.2f} MB → {output_size_mb:.2f} MB ({reduction:.0f}% reduction)")

    return output_path
