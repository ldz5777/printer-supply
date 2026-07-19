"""Pydantic 请求/响应模型"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Auth ====================

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginRequest(BaseModel):
    department: str
    applicant: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # "admin" | "user"
    username: Optional[str] = None  # admin username
    department: Optional[str] = None  # user department
    applicant: Optional[str] = None  # user name


# ==================== Department ====================

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class DepartmentResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Supply ====================

class SupplyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="硒鼓/墨盒")
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(default=13.0, ge=0, le=100)
    date: Optional[str] = None


class SupplyUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    quantity: Optional[int] = None
    remaining: Optional[int] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None


class SupplyResponse(BaseModel):
    id: int
    name: str
    type: str
    quantity: int
    remaining: int
    unit_price: float
    unit_price_without_tax: Optional[float] = None
    tax_rate: float
    total_cost: float
    total_cost_without_tax: Optional[float] = None
    date: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Allocation ====================

class AllocationCreate(BaseModel):
    supply_id: int
    department: str
    quantity: int = Field(..., gt=0)


class AllocationShareRequest(BaseModel):
    supply_ids: List[int]
    department_ids: List[int]  # actually department names in the DB
    method: str  # "equal" | "custom"
    date: Optional[str] = None
    custom_ratios: Optional[dict] = None  # {f"{supply_id}-{dept}": quantity}


class AllocationResponse(BaseModel):
    id: int
    supply_id: int
    supply_name: str
    department: str
    quantity: int
    unit_price: float
    cost: float
    date: str
    method: str
    is_share: bool
    source: str
    request_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Requisition Request ====================

class RequestCreate(BaseModel):
    department: str = ""
    applicant: str = ""
    supply_id: int
    quantity: int = Field(..., gt=0)
    reason: str = ""


class RequestAction(BaseModel):
    admin_remark: str = ""


class RequestResponse(BaseModel):
    id: int
    department: str
    applicant: str
    supply_id: int
    supply_name: str
    quantity: int
    reason: str
    status: str
    admin_remark: str
    request_date: str
    resolve_date: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Report ====================

class ReportSummary(BaseModel):
    total_supplies: int
    total_allocations: int
    total_departments: int
    total_supply_cost: float
    total_allocated_cost: float
    pending_requests: int
    low_stock_items: int


class DepartmentReport(BaseModel):
    department: str
    allocation_count: int
    total_quantity: int
    total_cost: float


class MonthlyReport(BaseModel):
    month: str
    purchase_amount: float
    allocation_amount: float


# ==================== Data Import/Export ====================

class ExportData(BaseModel):
    supplies: List[SupplyResponse]
    allocations: List[AllocationResponse]
    departments: List[DepartmentResponse]
    requests: List[RequestResponse]
    export_date: str
