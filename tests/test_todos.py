import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # 获取项目根目录的路径
sys.path.insert(0, str(PROJECT_ROOT))       # 将项目根目录添加到系统路径中，以便测试文件能够正确导入应用模块

TEST_DB_PATH = Path("data/test_todos.db")      # 定义测试数据库的路径

if TEST_DB_PATH.exists():       # 如果测试数据库文件存在，先删除它以确保每次测试都是在干净的环境下进行
    TEST_DB_PATH.unlink()   

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}" # 设置测试数据库路径
os.environ["SQL_ECHO"] = "false"    # 禁止测试时输出 SQL 语句

from main import app  # 导入 FastAPI 应用实例


def test_health_check():    # 测试健康检查接口
    with TestClient(app) as client: # 使用 TestClient 创建一个测试客户端实例
        response = client.get("/health")

    assert response.status_code == 200  # 断言响应状态码为 200，表示请求成功
    data = response.json()  # 将响应内容解析为 JSON 格式
    assert data["status"] == "ok"   # 断言响应数据中的 "status" 字段值为 "ok"，表示健康检查通过
    assert "time" in data   # 断言响应数据中包含 "time" 字段，表示返回了服务器时间


def test_create_todo(): # 测试创建 Todo 的接口
    with TestClient(app) as client:
        response = client.post(
            "/todos",
            json={
                "title": "Test create todo",
                "due_time": "today",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test create todo"
    assert data["completed"] is False
    assert data["due_time"] == "today"
    assert "id" in data


def test_todo_crud_flow():  # 测试 Todo 的完整 CRUD 流程
    with TestClient(app) as client: # 使用 TestClient 创建一个测试客户端实例
        create_response = client.post(
            "/todos",
            json={
                "title": "Test CRUD todo",
                "due_time": "tomorrow",
            },
        )

        assert create_response.status_code == 201   
        created = create_response.json()    
        todo_id = created["id"] # 获取创建的 Todo 的 ID

        get_response = client.get(f"/todos/{todo_id}")  # 获取刚创建的 Todo
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Test CRUD todo"
        
        patch_response = client.patch(  
            f"/todos/{todo_id}",
            json={
                "title": "Updated CRUD todo",
                "completed": True,
                "due_time": "tonight",
            },
        )   # 更新 Todo 的标题、完成状态和截止时间

        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["title"] == "Updated CRUD todo"
        assert updated["completed"] is True
        assert updated["due_time"] == "tonight"

        delete_response = client.delete(f"/todos/{todo_id}")    # 删除刚创建的 Todo
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Todo deleted"

        missing_response = client.get(f"/todos/{todo_id}")  # 尝试获取已删除的 Todo，应该返回 404
        assert missing_response.status_code == 404


def test_create_todo_with_empty_title_should_fail():    # 测试创建 Todo 时如果标题为空应该返回 422 错误
    with TestClient(app) as client:
        response = client.post(
            "/todos",
            json={
                "title": "",
            },
        )

    assert response.status_code == 422