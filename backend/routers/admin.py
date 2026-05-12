"""
Admin panel route.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Admin"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_panel(request: Request):
    try:
        return templates.TemplateResponse("admin.html", {"request": request})
    except Exception:
        return HTMLResponse("<h1>Admin panel not available.</h1>")
