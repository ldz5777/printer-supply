"""认证路由：登录、获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import AdminUser
from backend.schemas import AdminLoginRequest, UserLoginRequest, LoginResponse
from backend.auth import (
    verify_password, create_access_token,
    get_current_user, require_admin
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/admin/login", response_model=LoginResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_sync_db)):
    """管理员登录"""
    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": "admin",
        "username": user.username,
    })

    return LoginResponse(
        access_token=token,
        role="admin",
        username=user.username,
    )


@router.post("/user/login", response_model=LoginResponse)
def user_login(req: UserLoginRequest, db: Session = Depends(get_sync_db)):
    """用户登录（部门 + 姓名，无需密码）"""
    if not req.department or not req.applicant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部门和姓名不能为空"
        )

    token = create_access_token({
        "sub": f"user_{req.department}_{req.applicant}",
        "role": "user",
        "department": req.department,
        "applicant": req.applicant,
    })

    return LoginResponse(
        access_token=token,
        role="user",
        department=req.department,
        applicant=req.applicant,
    )


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "role": user.get("role"),
        "username": user.get("username"),
        "department": user.get("department"),
        "applicant": user.get("applicant"),
    }


from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/admin/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """修改管理员密码"""
    admin = db.query(AdminUser).filter(AdminUser.username == user.get("username")).first()
    if not admin or not verify_password(body.old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")

    from backend.auth import hash_password
    admin.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "密码修改成功"}
