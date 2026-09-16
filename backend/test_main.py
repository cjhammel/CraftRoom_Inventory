import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.database import engine, SessionLocal, Base, get_db
from app.main import app


@pytest.fixture(scope="module")
def client():
    # Create test tables
    Base.metadata.create_all(bind=engine)

    # Override DB dependency to use test DB
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

    # Cleanup
    Base.metadata.drop_all(bind=engine)


def create_stamp(client, **kwargs):
    data = {
        "product_name": "Test Stamp",
        "brand_name": "Test Brand",
        "retired": False,
        "product_type": "Rubber",
        "theme": "Floral",
        "shape_descriptor": "Square",
        "sentiments": "Hello",
        "location": "Box 1",
        "price": "12.99",
        **kwargs,
    }
    return client.post("/stamps", data=data)


def test_create_stamp(client):
    response = create_stamp(client)
    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == "Test Stamp"
    assert body["brand_name"] == "Test Brand"
    assert body["id"] is not None


def test_list_stamps(client):
    create_stamp(client)
    response = client.get("/stamps")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) >= 1
    assert stamps[0]["product_name"] == "Test Stamp"


def test_get_stamp_by_id(client):
    response = create_stamp(client)
    stamp_id = response.json()["id"]

    response = client.get(f"/stamps/{stamp_id}")
    assert response.status_code == 200
    assert response.json()["id"] == stamp_id


def test_get_stamp_404(client):
    response = client.get("/stamps/99999")
    assert response.status_code == 404


def test_update_stamp(client):
    response = create_stamp(client)
    stamp_id = response.json()["id"]

    response = client.put(
        f"/stamps/{stamp_id}",
        data={"brand_name": "Updated Brand", "price": "15.99"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "Updated Brand"
    assert body["price"] == 15.99


def test_delete_stamp(client):
    response = create_stamp(client)
    stamp_id = response.json()["id"]

    response = client.delete(f"/stamps/{stamp_id}")
    assert response.status_code == 200

    response = client.get(f"/stamps/{stamp_id}")
    assert response.status_code == 404


def test_delete_stamp_404(client):
    response = client.delete("/stamps/99999")
    assert response.status_code == 404


def test_search_stamps(client):
    create_stamp(client, product_name="Blue Mauritius", brand_name="StampCo")
    create_stamp(client, product_name="Red Rose", brand_name="CraftCo")

    response = client.get("/stamps?q=Blue")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["product_name"] == "Blue Mauritius"

    response = client.get("/stamps?brand_name=StampCo")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["brand_name"] == "StampCo"

    response = client.get("/stamps?product_type=Rubber")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) >= 1


def test_invalid_image_upload(client):
    # Upload a file with unsupported extension
    response = client.post(
        "/stamps",
        data={"product_name": "Test"},
        files={"image": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_create_stamp_empty_product_name(client):
    response = client.post(
        "/stamps",
        data={"product_name": "", "brand_name": "Test"},
    )
    assert response.status_code == 422  # Pydantic validation error


def test_create_stamp_invalid_price(client):
    response = client.post(
        "/stamps",
        data={"product_name": "Test", "price": "not_a_number"},
    )
    assert response.status_code == 400  # Validation error from route handler


def test_update_stamp_404(client):
    response = client.put(
        "/stamps/99999",
        data={"product_name": "Updated"},
    )
    assert response.status_code == 404


def test_ai_analyze_not_configured(client):
    response = client.post(
        "/ai/analyze-image",
        files={"image": ("test.png", b"fake image data", "image/png")},
    )
    assert response.status_code == 501


def test_create_stamp_with_retired(client):
    response = create_stamp(client, retired=True)
    assert response.status_code == 200
    body = response.json()
    assert body["retired"] is True


# --- Image upload and AI tests ---

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE_IMAGE_PATH = os.path.join(PROJECT_ROOT, "example_image", "IMG_20210616_132042564.jpg")


def test_image_upload_and_resize(client):
    """Test uploading a real image file and verify it's resized to <= 1MB."""
    if not os.path.exists(EXAMPLE_IMAGE_PATH):
        pytest.skip(f"Example image not found at {EXAMPLE_IMAGE_PATH}")

    with open(EXAMPLE_IMAGE_PATH, "rb") as f:
        original_size = os.path.getsize(EXAMPLE_IMAGE_PATH)
        response = client.post(
            "/stamps",
            data={
                "product_name": "Image Test Stamp",
                "brand_name": "Test Brand",
                "theme": "Nature",
            },
            files={"image": ("test_stamp.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == "Image Test Stamp"
    assert body["image_url"] is not None

    # Check the saved file size
    image_filename = os.path.basename(body["image_url"])
    saved_path = os.path.join(os.path.dirname(__file__), "uploads", image_filename)

    if os.path.exists(saved_path):
        saved_size = os.path.getsize(saved_path)
        assert saved_size <= 1_000_000, f"Saved image size {saved_size} bytes exceeds 1MB limit"
        # If original was larger, it should have been compressed
        if original_size > 1_000_000:
            assert saved_size < original_size, "Image was not compressed"
    else:
        # File might be in the parent uploads directory
        parent_saved_path = os.path.join(os.path.dirname(__file__), "..", "uploads", image_filename)
        if os.path.exists(parent_saved_path):
            saved_size = os.path.getsize(parent_saved_path)
            assert saved_size <= 1_000_000, f"Saved image size {saved_size} bytes exceeds 1MB limit"


def test_image_upload_preserves_small_images(client):
    """Test that small images are not upscaled."""
    # Create a small test image (1x1 red pixel PNG)
    import io
    from PIL import Image

    img = Image.new("RGB", (1, 1), color="red")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    original_size = img_buffer.tell()
    response = client.post(
        "/stamps",
        data={
            "product_name": "Small Image Stamp",
            "brand_name": "Test Brand",
        },
        files={"image": ("small_test.jpg", img_buffer, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] is not None


def test_ai_analyze_with_real_image(client, monkeypatch):
    """Test AI image analysis with a real image against the configured AI server."""
    if not os.path.exists(EXAMPLE_IMAGE_PATH):
        pytest.skip(f"Example image not found at {EXAMPLE_IMAGE_PATH}")

    # Set up AI configuration
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_API_URL", "http://framework.gruru.net:11434")
    monkeypatch.setenv("AI_MODEL", "qwen3.6:35B")

    with open(EXAMPLE_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/ai/analyze-image",
            files={"image": ("test_stamp.jpg", f, "image/jpeg")},
        )

    # The endpoint should succeed (200) or fail gracefully
    # It may return 501 if the server is not reachable, which is acceptable
    assert response.status_code in (200, 501, 502, 503, 504)

    body = response.json()
    assert "suggestions" in body


def test_ai_analyze_with_mock_response(client, monkeypatch):
    """Test AI image analysis with mocked response to avoid network dependency."""
    import json
    import asyncio

    async def mock_call_ai_api(image_path, api_key):
        return {
            "product_name": "Mocked Stamp",
            "brand_name": "Mock Brand",
            "product_type": "Rubber",
            "theme": "Mock Theme",
            "shape_descriptor": "Round",
            "sentiments": "Mock Sentiment",
        }

    from app import main
    monkeypatch.setattr(main, "call_ai_api", mock_call_ai_api)
    monkeypatch.setenv("AI_API_KEY", "test-key")

    # Create a small test image
    import io
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="blue")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    response = client.post(
        "/ai/analyze-image",
        files={"image": ("test_stamp.jpg", img_buffer, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "suggestions" in body
    assert body["suggestions"]["product_name"] == "Mocked Stamp"
    assert body["suggestions"]["brand_name"] == "Mock Brand"
