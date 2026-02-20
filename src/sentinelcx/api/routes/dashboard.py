"""Dashboard page route."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_STATIC_DIR = Path(__file__).parent.parent / "static"


@router.get("/dashboard")
async def dashboard_page() -> HTMLResponse:
    """Serve the real-time dashboard."""
    html_path = _STATIC_DIR / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
