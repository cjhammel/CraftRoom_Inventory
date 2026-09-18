import os
import uuid
import subprocess
import shutil
import logging
from typing import Optional

logger = logging.getLogger("craftroom")

_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
_upload_dir = os.getenv("UPLOAD_DIR", "../data/uploads")
UPLOAD_DIR = _upload_dir if os.path.isabs(_upload_dir) else os.path.join(_BACKEND_DIR, _upload_dir)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 1_000_000  # 1 MB target


def validate_image_file(file) -> Optional[str]:
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
    """Resize/compress image to <= MAX_FILE_SIZE using ffmpeg, preserving aspect ratio."""
    # Check current size
    file_size = os.path.getsize(input_path)
    logger.debug(f"Image size: {file_size} bytes")
    
    if file_size <= MAX_FILE_SIZE:
        # No resize needed, just copy
        logger.debug(f"Image under {MAX_FILE_SIZE} bytes, copying as-is")
        shutil.copy2(input_path, output_path)
        return output_path

    # Get original dimensions
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "json",
                input_path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        import json
        probe = json.loads(result.stdout)
        stream = probe["streams"][0]
        width = stream["width"]
        height = stream["height"]

        # Calculate max dimension to keep file <= 1 MB
        # Start with a reasonable dimension and scale down
        max_dim = min(width, height)
        quality = 85

        while max_dim > 50:
            scale = f"{max_dim}:-1"
            cmd = [
                "ffmpeg", "-i", input_path,
                "-vf", f"scale={scale}",
                "-q:v", str(quality),
                "-y",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)

            new_size = os.path.getsize(output_path)
            if new_size <= MAX_FILE_SIZE:
                return output_path

            # Reduce quality first, then dimensions
            if quality > 10:
                quality -= 10
            else:
                max_dim = max(max_dim // 2, 100)

        # Final fallback: heavy downscale
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", "scale=200:-1",
            "-q:v", "10",
            "-y",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)

    except FileNotFoundError:
        # ffmpeg/ffprobe not available — just copy the file
        logger.warning("ffmpeg/ffprobe not found, copying file without resize")
        shutil.copy2(input_path, output_path)
    except Exception as e:
        logger.error(f"Error during image resize: {e}", exc_info=True)
        shutil.copy2(input_path, output_path)

    return output_path
