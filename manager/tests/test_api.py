"""针对管理端 API 的测试用例，确保调度与队列逻辑正确。"""

from fastapi.testclient import TestClient
from manager.main import app, scheduler

client = TestClient(app)


def setup_function():
    """每个用例执行前清空调度器状态。"""
    scheduler.servers.clear()
    scheduler.tasks.clear()
    scheduler.queue.clear()


def register_server():
    """注册一个只有 L7 能力的测试服务器。"""
    resp = client.post(
        "/api/server/register",
        json={
            "server_id": "s1",
            "group": ["L7"],
            "max_concurrency": {"L7": 100},
            "ip": "10.0.0.1",
            "timestamp": 0,
        },
    )
    assert resp.status_code == 200


def test_queue_and_release():
    register_server()
    assert scheduler.servers["s1"].idle_concurrency["L7"] == 100

    # 提交第一个任务，占用 100 并发中的 50
    resp = client.post(
        "/api/task/submit",
        json={
            "targets": ["a.com"],
            "layer": "L7",
            "concurrency": 50,
            "duration": 60,
            "attack_method": "HTTP_Flood",
        },
    )
    first_task = resp.json()
    assert resp.status_code == 200
    assert first_task["status"] == "assigned"

    # 第二个任务请求 80 并发，因剩余 50 空闲而进入队列
    resp = client.post(
        "/api/task/submit",
        json={
            "targets": ["b.com"],
            "layer": "L7",
            "concurrency": 80,
            "duration": 60,
            "attack_method": "HTTP_Flood",
        },
    )
    second_task = resp.json()
    assert resp.status_code == 200
    assert second_task["status"] == "queued"
    assert scheduler.queue  # 队列中存在任务

    # 第一个任务完成，释放并发，应自动调度队列中的任务
    client.post(
        "/api/server/task_status",
        json={
            "server_id": "s1",
            "task_id": first_task["task_id"],
            "status": "done",
            "progress": 100,
            "logs": "",
            "timestamp": 0,
        },
    )
    queued = scheduler.tasks[second_task["task_id"]]
    assert queued.status == "assigned"
    assert not scheduler.queue  # 队列被清空


def test_index_page():
    """首页应返回前端页面内容。"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_get_task_detail():
    """提交任务后可查询其状态，查询不存在任务返回 404。"""
    register_server()
    resp = client.post(
        "/api/task/submit",
        json={
            "targets": ["a.com"],
            "layer": "L7",
            "concurrency": 10,
            "duration": 30,
            "attack_method": "HTTP_Flood",
        },
    )
    task_id = resp.json()["task_id"]
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["task_id"] == task_id

    resp = client.get("/api/task/not-exist")
    assert resp.status_code == 404

