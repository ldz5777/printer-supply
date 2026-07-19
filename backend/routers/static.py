"""静态文件服务 + 调试路由"""
import os, sys, mimetypes
from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()


def _get_static_dir():
    if getattr(sys, 'frozen', False):
        d = os.path.join(sys._MEIPASS, "static")
        if os.path.isdir(d):
            return d
    for d in [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
    ]:
        if os.path.isdir(d):
            return os.path.abspath(d)
    return os.getcwd()

_STATIC = _get_static_dir()


@router.get("/static/{filename:path}")
async def serve_static(filename: str):
    if not filename:
        filename = "login.html"
    fp = os.path.join(_STATIC, filename)
    if os.path.isfile(fp):
        mt, _ = mimetypes.guess_type(fp)
        return FileResponse(fp, media_type=mt or "text/html")
    return HTMLResponse(f"404: {fp}", status_code=404)


@router.get("/debug")
def debug_info():
    return {
        "STATIC_DIR": _STATIC,
        "exists": os.path.isdir(_STATIC),
        "files": os.listdir(_STATIC) if os.path.isdir(_STATIC) else [],
        "frozen": getattr(sys, 'frozen', False),
    }
