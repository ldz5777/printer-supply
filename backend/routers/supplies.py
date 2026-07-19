"""耗材管理路由"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import Supply
from backend.schemas import SupplyCreate, SupplyUpdate, SupplyResponse
from backend.auth import require_admin, require_user

router = APIRouter(prefix="/api/supplies", tags=["耗材管理"])


@router.get("", response_model=list[SupplyResponse])
def list_supplies(
    search: Optional[str] = Query(None, description="搜索关键词（名称）"),
    type: Optional[str] = Query(None, description="耗材类型"),
    available_only: bool = Query(False, description="仅显示有库存的"),
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取耗材列表"""
    query = db.query(Supply)

    if search:
        query = query.filter(Supply.name.contains(search))
    if type:
        query = query.filter(Supply.type == type)
    if available_only:
        query = query.filter(Supply.remaining > 0)

    return query.order_by(Supply.id.desc()).all()


@router.get("/{supply_id}", response_model=SupplyResponse)
def get_supply(
    supply_id: int,
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取单个耗材"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="耗材不存在")
    return supply


@router.post("", response_model=SupplyResponse, status_code=status.HTTP_201_CREATED)
def create_supply(
    req: SupplyCreate,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """入库新耗材（管理员）"""
    price_without_tax = req.unit_price / (1 + req.tax_rate / 100)
    total_cost = req.quantity * req.unit_price
    total_cost_without_tax = req.quantity * price_without_tax

    supply = Supply(
        name=req.name,
        type=req.type,
        quantity=req.quantity,
        remaining=req.quantity,
        unit_price=req.unit_price,
        unit_price_without_tax=round(price_without_tax, 2),
        tax_rate=req.tax_rate,
        total_cost=round(total_cost, 2),
        total_cost_without_tax=round(total_cost_without_tax, 2),
        date=req.date or date.today().isoformat(),
    )
    db.add(supply)
    db.commit()
    db.refresh(supply)
    return supply


@router.put("/{supply_id}", response_model=SupplyResponse)
def update_supply(
    supply_id: int,
    req: SupplyUpdate,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """更新耗材信息（管理员）"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="耗材不存在")

    update_data = req.model_dump(exclude_unset=True)

    # 如果更新了数量或单价，重新计算 total_cost
    quantity = update_data.get("quantity", supply.quantity)
    unit_price = update_data.get("unit_price", supply.unit_price)
    tax_rate = update_data.get("tax_rate", supply.tax_rate)
    if "quantity" in update_data or "unit_price" in update_data or "tax_rate" in update_data:
        price_without_tax = unit_price / (1 + tax_rate / 100)
        update_data["total_cost"] = round(quantity * unit_price, 2)
        update_data["total_cost_without_tax"] = round(quantity * price_without_tax, 2)
        update_data["unit_price_without_tax"] = round(price_without_tax, 2)
        # 如果数量变了，同步更新 remaining
        if "quantity" in update_data and "remaining" not in update_data:
            delta = update_data["quantity"] - supply.quantity
            update_data["remaining"] = max(0, supply.remaining + delta)

    for key, value in update_data.items():
        setattr(supply, key, value)

    db.commit()
    db.refresh(supply)
    return supply


@router.delete("/{supply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supply(
    supply_id: int,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """删除耗材（管理员）"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="耗材不存在")
    db.delete(supply)
    db.commit()


@router.get("/types/list")
def get_supply_types(
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取所有耗材类型"""
    types = db.query(Supply.type).distinct().all()
    return [t[0] for t in types]
