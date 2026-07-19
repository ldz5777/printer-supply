"""领用申请路由：提交申请、审核通过/驳回"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import Supply, Allocation, RequisitionRequest
from backend.schemas import RequestCreate, RequestAction, RequestResponse
from backend.auth import require_admin, require_user

router = APIRouter(prefix="/api/requests", tags=["领用申请"])


@router.get("", response_model=list[RequestResponse])
def list_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    my_only: bool = Query(False, description="仅查看我的申请"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取申请列表"""
    query = db.query(RequisitionRequest)

    # 普通用户只能看自己部门的
    if user.get("role") == "user":
        query = query.filter(
            RequisitionRequest.department == user.get("department"),
            RequisitionRequest.applicant == user.get("applicant"),
        )

    if status_filter:
        query = query.filter(RequisitionRequest.status == status_filter)

    return query.order_by(RequisitionRequest.id.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    req: RequestCreate,
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """提交领用申请"""
    supply = db.query(Supply).filter(Supply.id == req.supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="耗材不存在")

    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="申请数量必须大于0")

    if req.quantity > supply.remaining:
        raise HTTPException(status_code=400, detail=f"库存不足！当前剩余：{supply.remaining}")

    # 如果是用户端，使用 token 中的信息
    department = user.get("department", req.department)
    applicant = user.get("applicant", req.applicant)

    request = RequisitionRequest(
        department=department,
        applicant=applicant,
        supply_id=supply.id,
        supply_name=supply.name,
        quantity=req.quantity,
        reason=req.reason,
        status="pending",
        request_date=date.today().isoformat(),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.put("/{request_id}/approve", response_model=RequestResponse)
def approve_request(
    request_id: int,
    body: RequestAction = RequestAction(),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """审批通过领用申请（管理员）"""
    req = db.query(RequisitionRequest).filter(RequisitionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已被处理")

    supply = db.query(Supply).filter(Supply.id == req.supply_id).first()
    if not supply:
        raise HTTPException(status_code=400, detail="关联耗材已不存在")
    if req.quantity > supply.remaining:
        raise HTTPException(status_code=400, detail=f"库存不足！当前剩余：{supply.remaining}")

    # 扣减库存
    supply.remaining -= req.quantity

    # 自动生成分配记录
    allocation = Allocation(
        supply_id=supply.id,
        supply_name=supply.name,
        department=req.department,
        quantity=req.quantity,
        unit_price=supply.unit_price,
        cost=round(req.quantity * supply.unit_price, 2),
        date=date.today().isoformat(),
        method="领用申请",
        is_share=False,
        source="requisition",
        request_id=req.id,
    )
    db.add(allocation)

    # 更新申请状态
    req.status = "approved"
    req.admin_remark = body.admin_remark
    req.resolve_date = date.today().isoformat()

    db.commit()
    db.refresh(req)
    return req


@router.put("/{request_id}/reject", response_model=RequestResponse)
def reject_request(
    request_id: int,
    body: RequestAction = RequestAction(),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """驳回领用申请（管理员）"""
    req = db.query(RequisitionRequest).filter(RequisitionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已被处理")

    req.status = "rejected"
    req.admin_remark = body.admin_remark
    req.resolve_date = date.today().isoformat()

    db.commit()
    db.refresh(req)
    return req


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(
    request_id: int,
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """取消申请（申请人或管理员可取消 pending 状态的申请）"""
    req = db.query(RequisitionRequest).filter(RequisitionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="只能取消待审核的申请")

    # 普通用户只能取消自己的
    if user.get("role") == "user":
        if req.department != user.get("department") or req.applicant != user.get("applicant"):
            raise HTTPException(status_code=403, detail="只能取消自己的申请")

    db.delete(req)
    db.commit()


@router.get("/pending-count")
def get_pending_count(
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """获取待审核申请数量（管理员）"""
    count = db.query(RequisitionRequest).filter(
        RequisitionRequest.status == "pending"
    ).count()
    return {"count": count}
