from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, List, Optional


class ServerRegisterRequest(BaseModel):
    """子服务器注册时上报的信息。"""

    server_id: str  # 唯一标识
    group: List[str]  # 服务器所属分组，如 L4/L7
    max_concurrency: Dict[str, int]  # 各分组最大并发
    ip: str  # 服务器 IP 地址
    timestamp: int  # 上报时间戳


class TaskSubmitRequest(BaseModel):
    """用户提交的压测任务参数。"""

    targets: List[str]  # 目标域名或 IP
    layer: str  # 压测层级 L4/L7
    concurrency: int  # 并发数
    duration: int  # 持续时间
    attack_method: str  # 攻击方法


class TaskStatusReport(BaseModel):
    """子服务器回传任务执行状态。"""

    server_id: str  # 子服务器 ID
    task_id: str  # 对应任务 ID
    status: str  # 当前状态
    progress: int  # 进度百分比
    logs: Optional[str] = None  # 日志信息
    timestamp: int  # 上报时间戳


class ServerInfo(BaseModel):
    """管理端记录的服务器信息。"""

    server_id: str  # 唯一标识
    group: List[str]  # 分组信息
    max_concurrency: Dict[str, int]  # 最大并发
    ip: str  # IP 地址
    idle_concurrency: Dict[str, int]  # 当前空闲并发


class Task(BaseModel):
    """调度器内部表示的任务状态。"""

    task_id: str
    request: TaskSubmitRequest
    assigned: Dict[str, int]
    status: str = "queued"
    progress: int = 0
