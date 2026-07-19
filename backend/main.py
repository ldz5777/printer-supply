"""
打印机耗材分配与费用分摊系统 — FastAPI 后端
============================================
启动方式:
    python run_server.py           # 从项目根目录一键启动
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

访问:
    管理端: http://localhost:8000/static/admin.html
    用户端: http://localhost:8000/static/user.html
    登录页: http://localhost:8000/static/login.html
"""
import os
import sys

# 确保项目根目录在 sys.path 中，以便支持直接运行 python main.py
# PyInstaller 打包后使用 sys._MEIPASS
if getattr(sys, 'frozen', False):
    _project_root = sys._MEIPASS
else:
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.database import init_db, get_sync_db
from backend.models import Supply, Allocation, Department, RequisitionRequest
from backend.auth import require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    init_db()
    yield


app = FastAPI(
    title="打印机耗材分配与费用分摊系统",
    description="企业内部打印机耗材管理、领用申请、费用分摊系统",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由模块 ====================
from backend.routers.auth import router as auth_router
from backend.routers.supplies import router as supplies_router
from backend.routers.allocations import router as allocations_router
from backend.routers.departments import router as departments_router
from backend.routers.requests import router as requests_router
from backend.routers.reports import router as reports_router

app.include_router(auth_router)
app.include_router(supplies_router)
app.include_router(allocations_router)
app.include_router(departments_router)
app.include_router(requests_router)
app.include_router(reports_router)
try:
    from backend.routers.static import router as static_router
    app.include_router(static_router)
    print(f"[OK] Static router loaded, routes: {[r.path for r in static_router.routes]}")
except Exception as e:
    print(f"[ERROR] Failed to load static router: {e}")
    import traceback
    traceback.print_exc()

# ==================== 数据导入导出 ====================

def _model_to_dict(obj):
    """SQLAlchemy 模型转字典"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@app.get("/api/data/export")
def export_data(
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """导出全部数据为 JSON（管理员）"""
    return {
        "supplies": [_model_to_dict(s) for s in db.query(Supply).all()],
        "allocations": [_model_to_dict(a) for a in db.query(Allocation).all()],
        "departments": [_model_to_dict(d) for d in db.query(Department).all()],
        "requests": [_model_to_dict(r) for r in db.query(RequisitionRequest).all()],
        "export_date": date.today().isoformat(),
        "version": "2.0.0",
    }


@app.post("/api/data/import")
def import_data(
    file: UploadFile = File(...),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """从 JSON 文件导入数据（管理员，会清空现有数据）"""
    import json
    data = json.loads(file.file.read())

    # 清空现有数据（注意顺序：先删外键关联表）
    for model in [RequisitionRequest, Allocation, Supply, Department]:
        db.query(model).delete()

    for d in data.get("departments", []):
        db.add(Department(id=d.get("id"), name=d["name"]))
    for s in data.get("supplies", []):
        db.add(Supply(**{k: v for k, v in s.items() if k != "created_at"}))
    for a in data.get("allocations", []):
        db.add(Allocation(**{k: v for k, v in a.items() if k != "created_at"}))
    for r in data.get("requests", []):
        db.add(RequisitionRequest(**{k: v for k, v in r.items() if k != "created_at"}))

    db.commit()
    return {"message": "数据导入成功", "departments": len(data.get("departments", [])),
            "supplies": len(data.get("supplies", [])),
            "allocations": len(data.get("allocations", [])),
            "requests": len(data.get("requests", []))}


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "version": "2.0.0"}


# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
