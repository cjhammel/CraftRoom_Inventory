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
