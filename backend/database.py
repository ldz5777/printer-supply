"""数据库连接和会话管理"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 数据库文件路径（默认在 backend 目录下）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "printer_supply.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 同步引擎（用于初始化）
SYNC_DATABASE_URL = f"sqlite:///{DB_PATH}"
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


# 启用外键约束
@event.listens_for(sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class Base(DeclarativeBase):
    pass


def get_sync_db():
    """获取同步数据库会话"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表 + 种子数据）"""
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)

    db = SyncSessionLocal()
    try:
        # 种子数据：默认管理员
        from backend.auth import hash_password
        existing = db.query(models.AdminUser).first()
        if not existing:
            db.add(models.AdminUser(
                username="admin",
                password_hash=hash_password("admin123")
            ))

        # 种子数据：默认部门
        dept_count = db.query(models.Department).count()
        if dept_count == 0:
            default_depts = [
                "办公室", "人力资源部", "授信审批部", "计划财务部",
                "运营管理部", "国际金融部", "公司业务部", "个人业务部",
                "信息科技部", "风险管理部", "纪委办公室", "信用卡中心",
                "内控合规部", "金融市场部", "零售一部", "零售三部",
                "公司一部", "公司二部", "公司三部", "公司七部",
                "营销九部", "营销十部", "网络金融部", "普惠金融部",
                "学府路支行", "南通大街支行", "哈西支行", "自贸区支行", "兴江路支行"
            ]
            for name in default_depts:
                db.add(models.Department(name=name))

        db.commit()
    finally:
        db.close()
