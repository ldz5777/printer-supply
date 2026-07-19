"""SQLAlchemy 数据模型"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


class AdminUser(Base):
    """管理员用户"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    """部门"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Supply(Base):
    """耗材库存"""
    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False, default="硒鼓/墨盒")
    quantity = Column(Integer, nullable=False, default=0)
    remaining = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0.0)
    unit_price_without_tax = Column(Float, nullable=True)
    tax_rate = Column(Float, default=13.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    total_cost_without_tax = Column(Float, nullable=True)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    allocations = relationship("Allocation", back_populates="supply", cascade="all, delete-orphan")
    requests = relationship("RequisitionRequest", back_populates="supply", cascade="all, delete-orphan")


class Allocation(Base):
    """耗材分配记录"""
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supply_id = Column(Integer, ForeignKey("supplies.id", ondelete="CASCADE"), nullable=False)
    supply_name = Column(String(200), nullable=False)
    department = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(String(20), nullable=False)
    method = Column(String(50), default="手动分配")
    is_share = Column(Boolean, default=False)
    source = Column(String(20), default="manual")  # 'manual' | 'requisition'
    request_id = Column(Integer, ForeignKey("requisition_requests.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    supply = relationship("Supply", back_populates="allocations")
    request = relationship("RequisitionRequest", back_populates="allocation", uselist=False)


class RequisitionRequest(Base):
    """领用申请"""
    __tablename__ = "requisition_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String(100), nullable=False, index=True)
    applicant = Column(String(100), nullable=False, index=True)
    supply_id = Column(Integer, ForeignKey("supplies.id", ondelete="CASCADE"), nullable=False)
    supply_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(Text, default="")
    status = Column(String(20), default="pending", index=True)  # pending | approved | rejected
    admin_remark = Column(Text, default="")
    request_date = Column(String(20), nullable=False)
    resolve_date = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    supply = relationship("Supply", back_populates="requests")
    allocation = relationship("Allocation", back_populates="request", uselist=False)
