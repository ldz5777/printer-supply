"""部门管理路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import Department
from backend.schemas import DepartmentCreate, DepartmentResponse
from backend.auth import require_admin, require_user, get_current_user
from typing import Optional

router = APIRouter(prefix="/api/departments", tags=["部门管理"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments(
    user: Optional[dict] = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """获取所有部门"""
    return db.query(Department).order_by(Department.id).all()


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    req: DepartmentCreate,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """添加部门（管理员）"""
    existing = db.query(Department).filter(Department.name == req.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="部门已存在")

    dept = Department(name=req.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    dept_id: int,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """删除部门（管理员）"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    db.delete(dept)
    db.commit()
