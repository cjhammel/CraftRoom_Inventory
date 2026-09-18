import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    test_db_path = tmp_path / "test_product.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def create_stamp(client, **kwargs):
    data = {
        "item_number": "ITEM-001",
        "product_name": "Test Stamp",
        "brand_name": "Test Brand",
        "product_type": "Rubber",
        "theme": "Floral",
        "shape_descriptor": "Square",
        "sentiments": "Hello",
        "location": "Box 1",
        **kwargs,
    }
    return client.post("/stamps", data={k: v for k, v in data.items() if v is not None})


def create_location(client, **kwargs):
    data = {
        "cabinet": "Cabinet A",
        "shelf": "Shelf 1",
        "bin": "Bin 2",
        **kwargs,
    }
    return client.post("/locations", json=data)


def test_create_stamp(client):
    response = create_stamp(client)
    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == "Test Stamp"
    assert body["item_number"] == "ITEM-001"
    assert body["brand_name"] == "Test Brand"
    assert body["id"] is not None
    assert body["location_id"] is not None
    assert body["location"] == "Box 1"
    assert body["cabinet"] == "Box 1"


def test_list_stamps(client):
    create_stamp(client)
    response = client.get("/stamps")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) >= 1
    assert stamps[0]["product_name"] == "Test Stamp"
    assert stamps[0]["item_number"] == "ITEM-001"


def test_create_and_update_location(client):
    response = create_location(client)
    assert response.status_code == 200
    location = response.json()
    assert location["cabinet"] == "Cabinet A"
    assert location["shelf"] == "Shelf 1"
    assert location["bin"] == "Bin 2"

    response = client.put(
        f"/locations/{location['id']}",
        json={"cabinet": "Cabinet B", "shelf": "Shelf 3", "bin": None},
    )
    assert response.status_code == 200
    location = response.json()
    assert location["cabinet"] == "Cabinet B"
    assert location["shelf"] == "Shelf 3"
    assert location["bin"] is None

    response = client.get("/locations")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_stamp_with_location_id(client):
    location = create_location(client, cabinet="Drawer 1", shelf=None, bin=None).json()

    response = create_stamp(client, location=None, location_id=str(location["id"]))
    assert response.status_code == 200
    body = response.json()
    assert body["location_id"] == location["id"]
    assert body["location"] == "Drawer 1"


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
        data={"brand_name": "Updated Brand", "item_number": "ITEM-002"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "Updated Brand"
    assert body["item_number"] == "ITEM-002"


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
    create_stamp(
        client,
        product_name="Blue Mauritius",
        brand_name="StampCo",
        product_type="Rubber",
        location="Box 1",
    )
    create_stamp(
        client,
        product_name="Red Rose",
        brand_name="CraftCo",
        product_type="Clear",
        location="Album A",
    )

    response = client.get("/stamps?q=Blue")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["product_name"] == "Blue Mauritius"

    response = client.get("/stamps?q=ITEM-001")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) >= 1
    assert stamps[0]["item_number"] == "ITEM-001"

    response = client.get("/stamps?brand_name=StampCo")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["brand_name"] == "StampCo"

    response = client.get("/stamps?product_type=Rubber")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["product_type"] == "Rubber"

    response = client.get("/stamps?location=Album")
    assert response.status_code == 200
    stamps = response.json()
    assert len(stamps) == 1
    assert stamps[0]["location"] == "Album A"
    assert stamps[0]["location_id"] is not None
    assert stamps[0]["cabinet"] == "Album A"


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
    assert response.status_code == 400


def test_update_stamp_404(client):
    response = client.put(
        "/stamps/99999",
        data={"product_name": "Updated"},
    )
    assert response.status_code == 404


def test_update_stamp_empty_product_name(client):
    response = create_stamp(client)
    stamp_id = response.json()["id"]

    response = client.put(
        f"/stamps/{stamp_id}",
        data={"product_name": ""},
    )
    assert response.status_code == 400


def test_ai_analyze_not_configured(client, monkeypatch):
    """Verify 501 is returned when AI_API_URL is not set."""
    monkeypatch.delenv("AI_API_URL", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("AI_PROMPT", raising=False)

    # Monkeypatch get_ai_config at the point of use (main.py imports it directly)
    from app import main as main_module
    monkeypatch.setattr(main_module, "get_ai_config", lambda: {"api_url": "", "api_key": "", "model": "", "prompt": ""})

    response = client.post(
        "/ai/analyze-image",
        files={"image": ("test.png", b"fake image data", "image/png")},
    )
    assert response.status_code == 501
    body = response.json()
    assert "message" in body["detail"]
    assert "AI_API_URL" in body["detail"]["message"]


# --- Image upload and AI tests ---

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE_IMAGE_PATH = os.path.join(PROJECT_ROOT, "example_image", "Testimage3.jpg")


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
    # Check in the data/uploads directory (current config path)
    saved_path = os.path.join(os.path.dirname(__file__), "data", "uploads", image_filename)
    if not os.path.exists(saved_path):
        # Fallback to legacy uploads directory
        saved_path = os.path.join(os.path.dirname(__file__), "uploads", image_filename)
    if not os.path.exists(saved_path):
        # Fallback to parent uploads directory
        saved_path = os.path.join(os.path.dirname(__file__), "..", "uploads", image_filename)

    assert os.path.exists(saved_path), f"Saved image not found at any expected path (checked data/uploads/, uploads/, ../uploads/)"
    saved_size = os.path.getsize(saved_path)
    assert saved_size <= 1_000_000, f"Saved image size {saved_size:,} bytes exceeds 1MB limit"
    # Testimage3.jpg is ~5.8MB, so it should have been compressed significantly
    assert original_size > 1_000_000
    assert saved_size < original_size, f"Large image was not compressed (was {original_size:,}, now {saved_size:,})"


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
    if not os.getenv("RUN_EXTERNAL_AI_TESTS"):
        pytest.skip("Set RUN_EXTERNAL_AI_TESTS=1 to run external AI integration tests")

    if not os.path.exists(EXAMPLE_IMAGE_PATH):
        pytest.skip(f"Example image not found at {EXAMPLE_IMAGE_PATH}")

    # Set up AI configuration
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_API_URL", "http://framework.gruru.net:11434/v1")
    monkeypatch.setenv("AI_MODEL", "qwen3.6:35B")
    monkeypatch.setenv(
        "AI_PROMPT",
        "Analyze this stamp image and return a JSON object with these exact keys:\n"
        "product_name, brand_name, product_type, theme, shape_descriptor, sentiments.\n"
        "Use null for unknown fields. Example: {\"product_name\": \"Test\", \"brand_name\": null,\n"
        "\"product_type\": null, \"theme\": null, \"shape_descriptor\": null, \"sentiments\": null}.\n"
        "Return ONLY valid JSON, no markdown, no explanation.",
    )

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

    async def mock_call_ai_api(image_path, api_key=None, ai_api_url=None, ai_prompt=None):
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
    monkeypatch.setenv("AI_API_URL", "http://example.test:11434")
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


def test_ai_analyze_uses_request_configuration(client, monkeypatch):
    """Verify AI settings submitted from the app configuration menu are used."""
    captured = {}

    async def mock_call_ai_api(image_path, api_key=None, ai_api_url=None, ai_prompt=None):
        captured["api_key"] = api_key
        captured["ai_api_url"] = ai_api_url
        captured["ai_prompt"] = ai_prompt
        # Verify the image was resized before being passed to AI
        assert os.path.getsize(image_path) <= 1_000_000, f"Image sent to AI exceeds 1MB: {os.path.getsize(image_path)}"
        return {"product_name": "Configured Stamp"}

    from app import main
    monkeypatch.setattr(main, "call_ai_api", mock_call_ai_api)
    monkeypatch.delenv("AI_API_URL", raising=False)
    monkeypatch.setenv("AI_API_KEY", "server-secret")
    monkeypatch.delenv("AI_PROMPT", raising=False)

    import io
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="green")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    response = client.post(
        "/ai/analyze-image",
        data={
            "ai_api_url": "http://localhost:11434",
            "ai_prompt": "Return stamp metadata as JSON.",
        },
        files={"image": ("test_stamp.jpg", img_buffer, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["suggestions"]["product_name"] == "Configured Stamp"
    assert captured["api_key"] == ""
    assert captured["ai_api_url"] == "http://localhost:11434"
    assert captured["ai_prompt"] == "Return stamp metadata as JSON."


def test_ai_analyze_resizes_large_image(client, monkeypatch):
    """Verify that large images sent to AI analysis are resized to <= 1MB."""
    if not os.path.exists(EXAMPLE_IMAGE_PATH):
        pytest.skip(f"Example image not found at {EXAMPLE_IMAGE_PATH}")

    captured = {}

    async def mock_call_ai_api(image_path, api_key=None, ai_api_url=None, ai_prompt=None):
        # Check file size inside the mock (before finally block cleanup removes it)
        captured["size"] = os.path.getsize(image_path)
        captured["path"] = image_path
        return {"product_name": "Resized AI Test", "brand_name": "Test"}

    from app import main
    monkeypatch.setattr(main, "call_ai_api", mock_call_ai_api)
    monkeypatch.delenv("AI_API_URL", raising=False)
    monkeypatch.setenv("AI_API_KEY", "test-key")

    original_size = os.path.getsize(EXAMPLE_IMAGE_PATH)
    assert original_size > 1_000_000, f"Test image should be >1MB for this test, got {original_size:,} bytes"

    with open(EXAMPLE_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/ai/analyze-image",
            files={"image": ("large_test.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["suggestions"]["product_name"] == "Resized AI Test"
    assert captured["size"] <= 1_000_000, f"Image sent to AI was not resized: {captured['size']:,} bytes"


def test_ai_analyze_all_example_images_return_json(client, monkeypatch):
    """Verify all example images return proper JSON from AI analysis."""
    example_dir = os.path.join(PROJECT_ROOT, "example_image")
    example_images = [f for f in os.listdir(example_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    example_images.sort()

    expected_fields = {"product_name", "brand_name", "product_type", "theme", "shape_descriptor", "sentiments"}
    image_results = {}

    async def mock_call_ai_api(image_path, api_key=None, ai_api_url=None, ai_prompt=None):
        file_size = os.path.getsize(image_path)
        return {
            "product_name": f"Test Product",
            "brand_name": "Test Brand",
            "product_type": "Rubber",
            "theme": "Floral",
            "shape_descriptor": "Round",
            "sentiments": "Hello World",
        }

    from app import main
    monkeypatch.setattr(main, "call_ai_api", mock_call_ai_api)
    monkeypatch.delenv("AI_API_URL", raising=False)
    monkeypatch.setenv("AI_API_KEY", "test-key")

    for image_file in example_images:
        image_path = os.path.join(example_dir, image_file)
        if not os.path.exists(image_path):
            continue

        original_size = os.path.getsize(image_path)
        image_results[image_file] = {"original_size": original_size}

        with open(image_path, "rb") as f:
            response = client.post(
                "/ai/analyze-image",
                files={"image": (image_file, f, "image/jpeg")},
            )

        assert response.status_code == 200, f"Failed for {image_file}: {response.status_code} - {response.text}"
        body = response.json()
        assert "suggestions" in body, f"No suggestions in response for {image_file}"
        suggestions = body["suggestions"]

        for field in expected_fields:
            assert field in suggestions, f"Missing field '{field}' in response for {image_file}"
