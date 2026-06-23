import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine


""" 
连接 SQLite 数据库
"""
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/todos.db")
SQL_ECHO = os.getenv("SQL_ECHO", "true").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)