"""
数据库基础配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

# 数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/llamacontroller.db"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # 设置为 True 可以看到 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建声明式基类
Base = declarative_base()


def get_db() -> Generator:
    """
    获取数据库会话的依赖注入函数
    
    用于 FastAPI 依赖注入:
    ```python
    @app.get("/")
    def read_root(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库（创建所有表）
    """
    # 导入所有模型以确保它们被注册
    from llamacontroller.db import models  # noqa: F401
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """
    重置数据库（删除并重新创建所有表）
    
    警告: 这会删除所有数据！仅用于开发/测试
    """
    from llamacontroller.db import models  # noqa: F401
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
