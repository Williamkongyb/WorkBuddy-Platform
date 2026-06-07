from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declaritive_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库URL（默认使用SQLite）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workbuddy.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# 创建SessionLocal类（用于创建数据库会话）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类（用于创建数据库模型）
Base = declaritive_base()

# 依赖注入：获取数据库会话
def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有数据库表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功！")


def init_db():
    """初始化数据库"""
    # 导入所有模型（确保被Base识别）
    from app.models import models
    
    # 创建表
    create_tables()
    
    # 创建初始数据（可选）
    db = SessionLocal()
    try:
        # 这里可以添加初始数据
        pass
    finally:
        db.close()
