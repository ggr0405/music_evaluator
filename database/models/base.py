from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库配置
DATABASE_URL = "sqlite:///data/music_evaluator.db"

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)

    # 创建所有表
    Base.metadata.create_all(bind=engine)