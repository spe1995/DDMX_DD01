from __future__ import annotations
from typing import Dict, List
from uuid import uuid4

from .models import TaskSubmitRequest, ServerInfo, Task


class Scheduler:
    """简易调度器，负责服务器注册、任务分配和队列管理"""

    def __init__(self):
        # 已注册的所有子服务器
        self.servers: Dict[str, ServerInfo] = {}
        # 所有任务记录
        self.tasks: Dict[str, Task] = {}
        # 因资源不足暂时排队的任务
        self.queue: List[Task] = []

    # 注册服务器
    def register_server(self, server: ServerInfo):
        """登记子服务器的能力信息。"""
        self.servers[server.server_id] = server

    # 提交任务
    def submit_task(self, req: TaskSubmitRequest) -> Task:
        """创建任务对象并尝试立即分配。"""
        task_id = uuid4().hex
        task = Task(task_id=task_id, request=req, assigned={})
        self.tasks[task_id] = task
        self.dispatch_task(task)
        return task

    # 按层级分发任务到服务器
    def dispatch_task(self, task: Task):
        """根据服务器空闲并发量分配任务。"""
        layer = task.request.layer
        needed = task.request.concurrency
        assigned = 0
        # 以空闲并发从大到小排序，优先使用资源多的服务器
        servers = sorted(
            [s for s in self.servers.values() if layer in s.group],
            key=lambda s: s.idle_concurrency.get(layer, 0),
            reverse=True,
        )
        for s in servers:
            idle = s.idle_concurrency.get(layer, 0)
            if idle <= 0:
                continue
            # 每次尽量用尽单台服务器的剩余并发
            use = min(idle, needed - assigned)
            if use > 0:
                s.idle_concurrency[layer] -= use
                task.assigned[s.server_id] = use
                assigned += use
            if assigned >= needed:
                break
        # 未分配完则排入队列等待
        if assigned < needed:
            task.status = "queued"
            self.queue.append(task)
        else:
            task.status = "assigned"

    # 更新进度并释放资源
    def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度，完成后释放并发并尝试调度队列。"""
        task = self.tasks.get(task_id)
        if not task:
            return
        task.progress = progress
        if progress >= 100:
            task.status = "done"
            # 任务完成后归还已分配的并发资源
            layer = task.request.layer
            for server_id, amount in task.assigned.items():
                server = self.servers.get(server_id)
                if server:
                    server.idle_concurrency[layer] = (
                        server.idle_concurrency.get(layer, 0) + amount
                    )
            # 资源释放后尝试调度队列中的任务
            self.try_dispatch_queue()

    def try_dispatch_queue(self):
        """释放资源后再次尝试分配队列中的任务。"""
        for task in list(self.queue):
            self.queue.remove(task)
            self.dispatch_task(task)

