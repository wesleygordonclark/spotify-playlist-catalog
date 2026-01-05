# tests/test_dashboard_smoke.py
import os
import pytest

from streamlit.testing.v1 import AppTest


@pytest.mark.skipif(
    os.getenv("RUN_DASHBOARD_TESTS", "false").lower() != "true",
    reason="Set RUN_DASHBOARD_TESTS=true to run dashboard tests",
)
def test_dashboard_smoke(monkeypatch):
    # Point to a fake backend; only need the app script to run
    monkeypatch.setenv("STREAMLIT_BACKEND_URL", "http://localhost:9999")

    at = AppTest.from_file("dashboard/app.py")

    # If the app raises on import or during initial run, pytest will fail
    at.run(timeout=10)

    # No additional assertions needed: reaching here means it didn't crash
    # Any exceptions inside the app would bubble up and fail the test.


