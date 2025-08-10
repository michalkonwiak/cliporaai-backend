# ruff: noqa: S101
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectStatus


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, db: AsyncSession, token_headers: dict[str, str]) -> None:
    payload = {
        "name": "My Project",
        "description": "Desc",
        "project_type": "dynamic",
    }
    resp = await client.post("/api/v1/projects", json=payload, headers=token_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] > 0
    assert data["name"] == payload["name"]
    assert data["project_type"].lower() == payload["project_type"]
    assert data["status"] in {s.lower() for s in [s.value for s in ProjectStatus]}


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, db: AsyncSession, token_headers: dict[str, str]) -> None:
    # Create two projects
    for i in range(2):
        payload = {
            "name": f"Project {i}",
            "description": None,
            "project_type": "dynamic",
        }
        resp = await client.post("/api/v1/projects", json=payload, headers=token_headers)
        assert resp.status_code == 201
    # List
    resp = await client.get("/api/v1/projects", headers=token_headers)
    assert resp.status_code == 200
    arr = resp.json()
    assert isinstance(arr, list)
    assert len(arr) >= 2


@pytest.mark.asyncio
async def test_get_update_delete_project(client: AsyncClient, db: AsyncSession, token_headers: dict[str, str]) -> None:
    # Create one
    payload = {"name": "To Edit", "description": "", "project_type": "dynamic"}
    r = await client.post("/api/v1/projects", json=payload, headers=token_headers)
    assert r.status_code == 201
    project_id = r.json()["id"]

    # Get
    r = await client.get(f"/api/v1/projects/{project_id}", headers=token_headers)
    assert r.status_code == 200
    assert r.json()["id"] == project_id

    # Update
    upd = {"name": "Renamed", "description": "New desc"}
    r = await client.patch(f"/api/v1/projects/{project_id}", json=upd, headers=token_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Renamed"
    assert data["description"] == "New desc"

    # Delete
    r = await client.delete(f"/api/v1/projects/{project_id}", headers=token_headers)
    assert r.status_code == 204

    # Ensure 404 after delete
    r = await client.get(f"/api/v1/projects/{project_id}", headers=token_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_ownership_enforced(client: AsyncClient, db: AsyncSession, token_headers: dict[str, str], superuser_token_headers: dict[str, str]) -> None:
    # superuser creates project (different user)
    payload = {"name": "Admin Project", "project_type": "dynamic"}
    r = await client.post("/api/v1/projects", json=payload, headers=superuser_token_headers)
    assert r.status_code == 201
    pid = r.json()["id"]

    # regular user cannot access it
    r = await client.get(f"/api/v1/projects/{pid}", headers=token_headers)
    assert r.status_code == 403

    # same for update/delete
    r = await client.patch(f"/api/v1/projects/{pid}", json={"name": "x"}, headers=token_headers)
    assert r.status_code == 403
    r = await client.delete(f"/api/v1/projects/{pid}", headers=token_headers)
    assert r.status_code == 403
