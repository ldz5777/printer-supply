"""耗材分配与费用分摊路由"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import Supply, Allocation
from backend.schemas import (
    AllocationCreate, AllocationShareRequest, AllocationResponse,
)
from backend.auth import require_admin, require_user

router = APIRouter(prefix="/api/allocations", tags=["分配与分摊"])


@router.get("", response_model=list[AllocationResponse])
def list_allocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取分配记录（分页 + 筛选）"""
    query = db.query(Allocation)

    # 如果是普通用户，只能看自己部门的
    if user.get("role") == "user":
        query = query.filter(Allocation.department == user.get("department"))

    if department:
        query = query.filter(Allocation.department == department)
    if search:
        query = query.filter(Allocation.supply_name.contains(search))

    total = query.count()
    items = query.order_by(Allocation.id.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    return items


@router.post("", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(
    req: AllocationCreate,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """手动分配耗材（管理员）"""
    supply = db.query(Supply).filter(Supply.id == req.supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="耗材不存在")
    if req.quantity > supply.remaining:
        raise HTTPException(status_code=400, detail=f"库存不足！剩余：{supply.remaining}")

    allocation = Allocation(
        supply_id=supply.id,
        supply_name=supply.name,
        department=req.department,
        quantity=req.quantity,
        unit_price=supply.unit_price,
        cost=round(req.quantity * supply.unit_price, 2),
        date=date.today().isoformat(),
        method="手动分配",
        is_share=False,
        source="manual",
    )

    supply.remaining -= req.quantity
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


@router.post("/share", response_model=list[AllocationResponse])
def share_allocations(
    req: AllocationShareRequest,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """批量费用分摊（管理员）"""
    if not req.supply_ids:
        raise HTTPException(status_code=400, detail="请选择要分摊的耗材")
    if not req.department_ids:
        raise HTTPException(status_code=400, detail="请选择分摊部门")

    supplies = db.query(Supply).filter(Supply.id.in_(req.supply_ids)).all()
    if len(supplies) != len(req.supply_ids):
        raise HTTPException(status_code=400, detail="部分耗材不存在")

    share_date = req.date or date.today().isoformat()
    allocations = []

    if req.method == "equal":
        # 平均分摊
        dept_count = len(req.department_ids)
        for supply in supplies:
            share_qty_per_dept = supply.quantity // dept_count
            remainder = supply.quantity % dept_count
            share_amount_per_dept = (supply.total_cost_without_tax or supply.total_cost) / dept_count

            for i, dept in enumerate(req.department_ids):
                qty = share_qty_per_dept + (1 if i < remainder else 0)
                if qty <= 0:
                    continue
                alloc = Allocation(
                    supply_id=supply.id,
                    supply_name=supply.name,
                    department=dept,
                    quantity=qty,
                    unit_price=supply.unit_price_without_tax or supply.unit_price,
                    cost=round(share_amount_per_dept, 2),
                    date=share_date,
                    method="平均分摊",
                    is_share=True,
                    source="manual",
                )
                db.add(alloc)
                allocations.append(alloc)

            supply.remaining = 0

    elif req.method == "custom":
        # 自定义数量
        if not req.custom_ratios:
            raise HTTPException(status_code=400, detail="请设置自定义分摊数量")

        for supply in supplies:
            total_allocated = 0
            for dept in req.department_ids:
                key = f"{supply.id}-{dept}"
                qty = int(req.custom_ratios.get(key, 0))
                if qty <= 0:
                    continue
                if total_allocated + qty > supply.remaining:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{supply.name} 库存不足，剩余 {supply.remaining}"
                    )

                price_wo_tax = supply.unit_price_without_tax or (supply.unit_price / (1 + supply.tax_rate / 100))
                alloc = Allocation(
                    supply_id=supply.id,
                    supply_name=supply.name,
                    department=dept,
                    quantity=qty,
                    unit_price=supply.unit_price_without_tax or supply.unit_price,
                    cost=round(qty * price_wo_tax, 2),
                    date=share_date,
                    method="自定义数量",
                    is_share=True,
                    source="manual",
                )
                db.add(alloc)
                allocations.append(alloc)
                total_allocated += qty

            supply.remaining = max(0, supply.remaining - total_allocated)
    else:
        raise HTTPException(status_code=400, detail="不支持的分摊方式")

    db.commit()
    for a in allocations:
        db.refresh(a)
    return allocations


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allocation(
    allocation_id: int,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """删除分配记录并恢复库存（管理员）"""
    alloc = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="分配记录不存在")

    # 恢复库存
    supply = db.query(Supply).filter(Supply.id == alloc.supply_id).first()
    if supply:
        supply.remaining += alloc.quantity

    db.delete(alloc)
    db.commit()
