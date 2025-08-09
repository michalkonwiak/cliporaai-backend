# ruff: noqa: S101
import pytest
import httpx
from typing import Any, AsyncGenerator


from app.main import app
from app.dependencies import get_db, get_redis_client, get_s3_client


class _FakeRedisOK:
    async def ping(self) -> bool:  # pragma: no cover - trivial
        return True


class _FakeRedisFail:
    async def ping(self) -> bool:  # pragma: no cover - trivial
        return False


class _FakeS3OK:
    async def head_bucket(self, Bucket: str) -> None:  # pragma: no cover - trivial
        return None


class _FakeS3Fail:
    async def head_bucket(self, Bucket: str) -> None:  # pragma: no cover - trivial
        raise Exception("S3 error")


@pytest.mark.asyncio
async def test_live_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_all_ok(client: httpx.AsyncClient) -> None:
    # Override external dependencies with healthy fakes
    app.dependency_overrides[get_redis_client] = lambda: _FakeRedisOK()
    app.dependency_overrides[get_s3_client] = lambda: _FakeS3OK()

    try:
        resp = await client.get("/api/v1/health")
    finally:
        # Clean up overrides to not leak into other tests
        app.dependency_overrides.pop(get_redis_client, None)
        app.dependency_overrides.pop(get_s3_client, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["services"]["app"]["status"] == "ok"
    assert body["services"]["database"]["status"] == "ok"
    assert body["services"]["redis"]["status"] == "ok"
    assert body["services"]["localstack"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_redis_fail(client: httpx.AsyncClient) -> None:
    app.dependency_overrides[get_redis_client] = lambda: _FakeRedisFail()
    app.dependency_overrides[get_s3_client] = lambda: _FakeS3OK()
    try:
        resp = await client.get("/api/v1/health")
    finally:
        app.dependency_overrides.pop(get_redis_client, None)
        app.dependency_overrides.pop(get_s3_client, None)

    assert resp.status_code == 503
    body = resp.json()["detail"]
    assert body["status"] == "error"
    assert body["services"]["redis"]["status"] == "error"


@pytest.mark.asyncio
async def test_health_s3_fail(client: httpx.AsyncClient) -> None:
    app.dependency_overrides[get_redis_client] = lambda: _FakeRedisOK()
    app.dependency_overrides[get_s3_client] = lambda: _FakeS3Fail()
    try:
        resp = await client.get("/api/v1/health")
    finally:
        app.dependency_overrides.pop(get_redis_client, None)
        app.dependency_overrides.pop(get_s3_client, None)

    assert resp.status_code == 503
    body = resp.json()["detail"]
    assert body["status"] == "error"
    assert body["services"]["localstack"]["status"] == "error"


class _FailSession:
    async def execute(self, *_: Any, **__: Any) -> Any:  # pragma: no cover - trivial
        raise RuntimeError("DB error")


async def _failing_db() -> AsyncGenerator[Any, None]:
    yield _FailSession()


@pytest.mark.asyncio
async def test_health_db_fail(client: httpx.AsyncClient) -> None:
    # Override all deps: failing DB, healthy redis & s3
    app.dependency_overrides[get_db] = _failing_db
    app.dependency_overrides[get_redis_client] = lambda: _FakeRedisOK()
    app.dependency_overrides[get_s3_client] = lambda: _FakeS3OK()
    try:
        resp = await client.get("/api/v1/health")
    finally:
        # Restore original test DB override from tests.conftest by clearing here;
        # the conftest fixture re-sets it for new client instances.
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_redis_client, None)
        app.dependency_overrides.pop(get_s3_client, None)

    assert resp.status_code == 503
    body = resp.json()["detail"]
    assert body["status"] == "error"
    assert body["services"]["database"]["status"] == "error"


@pytest.mark.asyncio
async def test_ready_proxies_health(client: httpx.AsyncClient) -> None:
    app.dependency_overrides[get_redis_client] = lambda: _FakeRedisOK()
    app.dependency_overrides[get_s3_client] = lambda: _FakeS3OK()
    try:
        resp = await client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.pop(get_redis_client, None)
        app.dependency_overrides.pop(get_s3_client, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
