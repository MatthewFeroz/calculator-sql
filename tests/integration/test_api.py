"""
Integration tests for the FastAPI endpoints in main.py.

FastAPI's TestClient sends real HTTP requests to the app in-process (no
live server needed), so these tests verify routing, Pydantic validation,
the operation logic, and the JSON response shapes all working together.
"""

import pytest
from fastapi.testclient import TestClient

import main as main_module
from main import app


@pytest.fixture
def client():
    """Provide a TestClient wired to the FastAPI app."""
    with TestClient(app) as client:
        yield client


def test_homepage_returns_html(client):
    """GET / serves the calculator page rendered from the Jinja2 template."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Calculator" in response.text


def test_health_endpoint(client):
    """GET /health responds with a 200 status for monitoring checks."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "endpoint, a, b, expected",
    [
        ("/add", 10, 5, 15),
        ("/add", -10, 5, -5),
        ("/subtract", 10, 5, 5),
        ("/subtract", 5, 10, -5),
        ("/multiply", 10, 5, 50),
        ("/multiply", 10, 0, 0),
        ("/divide", 10, 2, 5),
        ("/divide", 1, 4, 0.25),
    ],
    ids=[
        "add_positive",
        "add_negative",
        "subtract_positive",
        "subtract_negative_result",
        "multiply_positive",
        "multiply_by_zero",
        "divide_positive",
        "divide_fractional",
    ],
)
def test_operation_endpoints(client, endpoint, a, b, expected):
    """Each arithmetic endpoint returns 200 and the correct result."""
    response = client.post(endpoint, json={"a": a, "b": b})
    assert response.status_code == 200
    assert response.json()["result"] == expected


def test_divide_by_zero_returns_400(client):
    """POST /divide with b=0 returns a 400 error with a clear message."""
    response = client.post("/divide", json={"a": 10, "b": 0})
    assert response.status_code == 400
    assert "Cannot divide by zero!" in response.json()["error"]


@pytest.mark.parametrize("endpoint", ["/add", "/subtract", "/multiply", "/divide"])
def test_invalid_input_returns_400(client, endpoint):
    """Non-numeric input fails Pydantic validation and returns 400."""
    response = client.post(endpoint, json={"a": "not-a-number", "b": 5})
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.parametrize("endpoint", ["/add", "/subtract", "/multiply", "/divide"])
def test_missing_field_returns_400(client, endpoint):
    """A request missing the 'b' field fails validation and returns 400."""
    response = client.post(endpoint, json={"a": 10})
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.parametrize(
    "operation_name, endpoint, expected_status",
    [
        ("add", "/add", 400),
        ("subtract", "/subtract", 400),
        ("multiply", "/multiply", 400),
        ("divide", "/divide", 500),
    ],
    ids=["add_error", "subtract_error", "multiply_error", "divide_error"],
)
def test_unexpected_operation_errors_are_safe(
    client, monkeypatch, operation_name, endpoint, expected_status
):
    """Unexpected operation failures use the endpoint's documented safe response."""

    def fail_operation(*_args):
        raise RuntimeError("forced test failure")

    monkeypatch.setattr(main_module, operation_name, fail_operation)
    response = client.post(endpoint, json={"a": 10, "b": 5})

    assert response.status_code == expected_status
    if expected_status == 500:
        assert response.json() == {"error": "Internal Server Error"}
    else:
        assert response.json() == {"error": "forced test failure"}
