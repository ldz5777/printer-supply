"""报表统计路由"""
from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_sync_db
from backend.models import Supply, Allocation, RequisitionRequest, Department
from backend.schemas import ReportSummary, DepartmentReport, MonthlyReport
from backend.auth import require_admin, require_user

router = APIRouter(prefix="/api/reports", tags=["报表统计"])


@router.get("/summary", response_model=ReportSummary)
def get_summary(
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """获取首页统计汇总"""
    total_supplies = db.query(Supply).count()
    total_allocations = db.query(Allocation).count()
    total_departments = db.query(Department).count()
    total_supply_cost = db.query(func.coalesce(func.sum(Supply.total_cost), 0)).scalar()
    total_allocated_cost = db.query(func.coalesce(func.sum(Allocation.cost), 0)).scalar()
    pending_requests = db.query(RequisitionRequest).filter(
        RequisitionRequest.status == "pending"
    ).count()
    low_stock_items = db.query(Supply).filter(Supply.remaining == 0).count()

    return ReportSummary(
        total_supplies=total_supplies,
        total_allocations=total_allocations,
        total_departments=total_departments,
        total_supply_cost=round(float(total_supply_cost), 2),
        total_allocated_cost=round(float(total_allocated_cost), 2),
        pending_requests=pending_requests,
        low_stock_items=low_stock_items,
    )


@router.get("/by-department", response_model=list[DepartmentReport])
def get_by_department(
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """按部门汇总"""
    results = db.query(
        Allocation.department,
        func.count(Allocation.id).label("count"),
        func.coalesce(func.sum(Allocation.quantity), 0).label("qty"),
        func.coalesce(func.sum(Allocation.cost), 0).label("cost"),
    ).group_by(Allocation.department).order_by(func.sum(Allocation.cost).desc()).all()

    return [
        DepartmentReport(
            department=r[0],
            allocation_count=r[1],
            total_quantity=int(r[2]),
            total_cost=round(float(r[3]), 2),
        )
        for r in results
    ]


@router.get("/monthly", response_model=list[MonthlyReport])
def get_monthly(
    user: dict = Depends(require_user),
    db: Session = Depends(get_sync_db),
):
    """月度趋势（近12个月）"""
    monthly = defaultdict(lambda: {"purchase": 0.0, "allocation": 0.0})

    supplies = db.query(Supply).all()
    for s in supplies:
        try:
            month_key = s.date[:7]
            monthly[month_key]["purchase"] += s.total_cost
        except (ValueError, IndexError):
            pass

    allocations = db.query(Allocation).all()
    for a in allocations:
        try:
            month_key = a.date[:7]
            monthly[month_key]["allocation"] += a.cost
        except (ValueError, IndexError):
            pass

    sorted_months = sorted(monthly.keys())[-12:]

    return [
        MonthlyReport(
            month=m,
            purchase_amount=round(monthly[m]["purchase"], 2),
            allocation_amount=round(monthly[m]["allocation"], 2),
        )
        for m in sorted_months
    ]


@router.get("/export/{export_type}")
def export_report(
    export_type: str,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_sync_db),
):
    """导出报表数据"""
    if export_type == "supplies":
        supplies = db.query(Supply).order_by(Supply.id.desc()).all()
        return [
            {
                "入库日期": s.date, "耗材名称": s.name, "类型": s.type,
                "数量": s.quantity, "剩余": s.remaining,
                "含税单价": s.unit_price, "不含税单价": s.unit_price_without_tax,
                "税率": f"{s.tax_rate}%",
                "含税总价": s.total_cost, "不含税总价": s.total_cost_without_tax,
            }
            for s in supplies
        ]
    elif export_type == "allocations":
        allocs = db.query(Allocation).order_by(Allocation.id.desc()).all()
        return [
            {
                "日期": a.date, "耗材名称": a.supply_name, "部门": a.department,
                "数量": a.quantity, "单价": a.unit_price, "费用": a.cost,
                "方式": a.method, "来源": a.source,
            }
            for a in allocs
        ]
    elif export_type == "requests":
        reqs = db.query(RequisitionRequest).order_by(RequisitionRequest.id.desc()).all()
        status_map = {"pending": "待审核", "approved": "已通过", "rejected": "已驳回"}
        return [
            {
                "申请日期": r.request_date, "部门": r.department, "申请人": r.applicant,
                "耗材": r.supply_name, "数量": r.quantity, "理由": r.reason,
                "状态": status_map.get(r.status, r.status),
                "管理员备注": r.admin_remark, "处理日期": r.resolve_date,
            }
            for r in reqs
        ]
    else:
        return []
