from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    ServerRegisterRequest,
    TaskSubmitRequest,
    TaskStatusReport,
    ServerInfo,
)
from .scheduler import Scheduler

app = FastAPI(title="DDOS Pressure Test Manager")
# 单例调度器，管理所有服务器与任务
scheduler = Scheduler()

# 挂载静态页面，提供简单的前端界面
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    """返回内置的单页前端页面。"""
    return FileResponse(static_dir / "index.html")


@app.post("/api/server/register")
def register_server(req: ServerRegisterRequest):
    """子服务器向管理端注册自身能力。"""
    server = ServerInfo(
        server_id=req.server_id,
        group=req.group,
        max_concurrency=req.max_concurrency,
        ip=req.ip,
        idle_concurrency=req.max_concurrency.copy(),
    )
    scheduler.register_server(server)
    return {"status": "ok"}


@app.post("/api/task/submit")
def submit_task(req: TaskSubmitRequest):
    """用户提交压测任务。"""
    task = scheduler.submit_task(req)
    return {"task_id": task.task_id, "status": task.status, "assigned": task.assigned}


@app.post("/api/server/task_status")
def update_task_status(report: TaskStatusReport):
    """子服务器汇报任务进度。"""
    scheduler.update_task_progress(report.task_id, report.progress)
    return {"status": "ok"}


@app.get("/api/task/{task_id}")
def get_task(task_id: str):
    """查询任务执行状态。"""
    task = scheduler.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "assigned": task.assigned,
    }
