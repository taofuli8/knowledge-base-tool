import os
import pytest
from fastapi.testclient import TestClient

os.environ["KNOWLEDGE_DB_PATH"] = "test_knowledge.db"

from app.database import init_db
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    yield
    if os.path.exists("test_knowledge.db"):
        os.remove("test_knowledge.db")


client = TestClient(app)


def test_create_tutorial_entry():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Test Tutorial",
        "raw_content": "This is test content"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Tutorial"
    assert data["content_type"] == "tutorial"
    assert data["status"] == "pending"


def test_create_url_entry():
    resp = client.post("/api/entries", json={
        "content_type": "url",
        "url": "https://example.com",
        "title": "Example Site"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://example.com"


def test_create_github_entry():
    resp = client.post("/api/entries", json={
        "content_type": "github",
        "url": "https://github.com/example/repo",
        "title": "Example Repo",
        "raw_content": "# Example\nThis is a README"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "github" in data["url"]


def test_create_entry_missing_url():
    resp = client.post("/api/entries", json={
        "content_type": "url"
    })
    assert resp.status_code == 422


def test_create_entry_missing_content():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial"
    })
    assert resp.status_code == 422


def test_list_entries():
    resp = client.get("/api/entries")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 0


def test_get_entry():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Get Test",
        "raw_content": "content"
    })
    entry_id = resp.json()["id"]
    resp = client.get(f"/api/entries/{entry_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Test"


def test_get_entry_not_found():
    resp = client.get("/api/entries/99999")
    assert resp.status_code == 404


def test_update_entry():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Update Test",
        "raw_content": "content"
    })
    entry_id = resp.json()["id"]
    resp = client.put(f"/api/entries/{entry_id}", json={
        "title": "Updated Title",
        "summary": "This is a summary",
        "tags": ["test", "demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == "This is a summary"
    assert "test" in data["tags"]


def test_delete_entry():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Delete Test",
        "raw_content": "content"
    })
    entry_id = resp.json()["id"]
    resp = client.delete(f"/api/entries/{entry_id}")
    assert resp.status_code == 200
    resp = client.get(f"/api/entries/{entry_id}")
    assert resp.status_code == 404


def test_search_entries():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Searchable Tutorial",
        "raw_content": "unique search content xyz"
    })
    entry_id = resp.json()["id"]
    client.put(f"/api/entries/{entry_id}", json={"summary": "unique summary xyz"})

    resp = client.get("/api/entries/search", params={"q": "unique"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0


def test_search_with_type_filter():
    resp = client.get("/api/entries/search", params={"q": "tutorial", "content_type": "github"})
    assert resp.status_code == 200


def test_tags():
    client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Tag Test",
        "raw_content": "content"
    })
    client.put("/api/entries/1", json={"tags": ["python", "ai"]})

    resp = client.get("/api/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_stats():
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "url" in data
    assert "tutorial" in data
    assert "github" in data


def test_update_summary():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Summary Test",
        "raw_content": "content"
    })
    entry_id = resp.json()["id"]
    resp = client.post(f"/api/entries/{entry_id}/summary", params={"summary": "Test summary"})
    assert resp.status_code == 200


def test_get_entry_content():
    resp = client.post("/api/entries", json={
        "content_type": "tutorial",
        "title": "Content Test",
        "raw_content": "Raw content here"
    })
    entry_id = resp.json()["id"]
    resp = client.get(f"/api/entries/{entry_id}/content")
    assert resp.status_code == 200
    assert resp.json()["content"] == "Raw content here"
