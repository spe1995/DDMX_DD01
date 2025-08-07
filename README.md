# DDMX_DD01 示例项目

该项目演示一个“Python 管理端 + Go 子服务器”架构的压测系统基础代码，并提供了简易前端页面便于测试接口。

## 目录结构

- `manager/`：FastAPI 编写的管理端服务，负责服务器注册、任务提交与调度。
- `manager/static/`：内置的极简前端页面。
- `agent/`：Go 编写的子服务器示例，启动时向管理端注册并提供 `/run_task` 接口。
- `manager/tests/`：针对管理端接口的单元测试。

## 运行方法

### 管理端

```bash
pip install fastapi uvicorn pydantic pytest
uvicorn manager.main:app --reload
# 浏览器访问 http://localhost:8000/ 使用前端页面
```

### 子服务器

```bash
cd agent
go run .
```

### 运行测试

```bash
pytest
# Go 端编译检查
go build ./agent
```

以上代码仅为示例，未真正实现攻击行为，请勿用于非法用途。
