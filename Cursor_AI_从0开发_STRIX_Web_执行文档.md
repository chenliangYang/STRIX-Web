# Cursor AI 从 0 开发 STRIX Web 平台执行文档

版本：v1.1  
日期：2026-05-19  
目标读者：Cursor、Claude Code、Codex 等 AI 编程代理，以及负责验收的人类开发者

## 0. 如何使用这份文档

这不是普通需求文档，而是给 AI 开发代理使用的工程执行说明。推荐把本文件整体喂给 Cursor 作为项目上下文，然后按本文最后的“阶段提示词”逐段执行。

不要一次性让 AI 完成整个系统。更好的方式是：

1. 先让 AI 创建项目骨架和基础配置。
2. 再做数据库模型和迁移。
3. 再做认证、权限、任务 CRUD。
4. 再做 Runner、Strix 集成、WebSocket。
5. 最后做结果解析、仪表盘、交互式终端和系统管理。

每一阶段完成后必须运行测试、启动前后端、人工检查页面，再进入下一阶段。

## 1. 项目背景

用户已有 Debian/Ubuntu 环境中的 STRIX CLI，并已配置 API。现在需要把 STRIX 封装成 Web 平台，让用户可以通过浏览器创建扫描任务、执行扫描、实时查看扫描过程、查看扫描结果、管理白名单、管理用户和查看审计日志。

STRIX 有两种运行方式：

- 非交互模式：加 `-n`，会实时生成结构化日志或结果产物，适合作为 MVP 主链路。
- 交互模式：不加 `-n`，进入复杂 TUI。TUI 原始字节流包含 ANSI 控制码和屏幕刷新行为，不能可靠解析成普通 Web 表格，只能用 xterm.js 做浏览器终端镜像。

核心原则：

- 非交互模式负责结构化结果和平台主流程。
- 交互模式只负责终端镜像，不承诺自动结构化漏洞。
- 不要解析 TUI 字节流生成漏洞结果。

## 2. 技术栈固定

除非用户明确要求更换，否则按以下技术栈开发。

后端：

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- MySQL 8.0+
- Redis，使用已有云 Redis，代码仍需预留抽象
- Uvicorn
- Pydantic v2
- JWT 鉴权
- passlib/bcrypt 密码哈希
- PyMySQL 或 asyncmy，推荐先用 SQLAlchemy 同步引擎 + PyMySQL，降低 MVP 复杂度
- pytest

前端：

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- ECharts
- xterm.js
- markdown-it
- DOMPurify
- Vitest，可选

部署：

- 不强制使用 Docker Compose。
- MySQL 和 Redis 使用用户已部署的云服务器实例。
- 后端本地或服务器上启动 FastAPI，直接连接云 MySQL/Redis。
- 前端本地启动 Vite，生产构建后可由 Nginx 托管。
- 生产可用 Nginx + Uvicorn/Gunicorn + systemd。
- 云 MySQL/Redis 需要提前配置安全组、防火墙、账号权限和网络白名单。

## 3. 不可违反的架构决策

### 3.1 任务、运行、结果分离

必须拆分：

- `tasks`：用户创建的任务配置。
- `task_runs`：每次执行任务产生一条运行记录。
- `results`：运行结束后生成的项目结果摘要。
- `vulnerabilities`：结果中的漏洞明细。
- `artifacts`：运行产物文件索引。

禁止只用一张任务表承载所有数据。

### 3.2 WebSocket 使用边界

必须使用 WebSocket：

- 非交互扫描的实时事件推送。
- 交互式终端的 PTY 输入输出。
- 任务状态实时通知。

不使用 WebSocket：

- 登录。
- 任务创建、编辑、删除。
- 白名单管理。
- 用户管理。
- 结果列表查询。
- Markdown 详情读取。
- 审计日志查询。

原则：

- 页面初始数据走 REST。
- 实时增量走 WebSocket。
- WebSocket 断线后，前端必须能用 REST 补拉历史事件。

### 3.3 Redis 定位

本项目已有可用云 Redis，建议从第一版就接入 Redis，但只做轻量基础设施，不承载业务事实数据。

第一版建议使用 Redis 做：

- `DistributedLock`：防止同一任务被重复执行。
- `EventBus`：Runner 将任务状态和运行事件发布给 WebSocket 服务。
- 简单限流：登录、执行任务等敏感操作可做计数。

第一版可以暂缓使用 Redis 做复杂任务队列。若 API 和 Runner 仍在同一进程，`TaskQueue` 可以先用内存实现，但接口必须保留，后续可切换 Redis/RQ/Celery/Arq。

代码必须预留以下抽象：

- `TaskQueue`
- `DistributedLock`
- `EventBus`

生产建议使用 Redis 做：

- 任务队列。
- 分布式锁。
- Pub/Sub 或 Streams 广播运行事件。
- Runner 心跳。
- 限流计数。

Redis 不能作为业务事实来源。最终任务、运行、结果、漏洞、审计日志必须落 MySQL。

### 3.4 Runner 边界

HTTP 请求不能直接长期执行 STRIX。

必须实现 Runner 抽象：

- API 负责鉴权、白名单校验、创建运行记录。
- Runner 负责启动、停止、监控 STRIX。
- Runner 写数据库状态。
- Runner 推送事件到 EventBus。

MVP 可以 API 和 Runner 在同一进程，但代码层面必须分离。

### 3.5 文件路径安全

数据库只能保存相对 artifact 路径。前端不能接触服务器绝对路径。

后端读取 Markdown 或日志时，必须校验目标文件位于该 run 的 artifact 根目录下，禁止任意文件读取。

### 3.6 命令执行安全

启动 STRIX 时禁止 `shell=True`，必须使用参数数组。

示例：

```python
args = [settings.STRIX_BIN, "-n", "--target", task.target]
```

禁止：

```python
subprocess.Popen(f"strix -n --target {target}", shell=True)
```

## 4. 推荐仓库结构

```text
strix-web/
  README.md
  .env.example
  backend/
    pyproject.toml
    alembic.ini
    app/
      main.py
      core/
        config.py
        security.py
        errors.py
        logging.py
        enums.py
      db/
        session.py
        base.py
        seed.py
      models/
        user.py
        task.py
        task_run.py
        run_event.py
        result.py
        vulnerability.py
        artifact.py
        whitelist.py
        audit_log.py
      schemas/
        auth.py
        common.py
        task.py
        task_run.py
        result.py
        system.py
        websocket.py
      api/
        deps.py
        routes/
          auth.py
          dashboard.py
          tasks.py
          runs.py
          results.py
          users.py
          whitelists.py
          audit_logs.py
          websockets.py
      services/
        auth_service.py
        audit_service.py
        dashboard_service.py
        task_service.py
        run_service.py
        result_service.py
        user_service.py
        whitelist_service.py
      strix/
        command_builder.py
        runner.py
        process_registry.py
        event_tailer.py
        result_parser.py
        terminal_session.py
        fake_strix.py
      infra/
        queue.py
        lock.py
        event_bus.py
      storage/
        path_manager.py
        artifact_store.py
      tests/
    alembic/
      versions/
  frontend/
    package.json
    vite.config.ts
    src/
      main.ts
      App.vue
      router/
        index.ts
        guards.ts
      stores/
        auth.ts
      api/
        http.ts
        auth.ts
        dashboard.ts
        tasks.ts
        runs.ts
        results.ts
        system.ts
        websocket.ts
      layouts/
        AdminLayout.vue
        LoginLayout.vue
      components/
        AppSidebar.vue
        AppHeader.vue
        RiskTag.vue
        StatusTag.vue
        ConfirmAction.vue
        TerminalPanel.vue
        MarkdownViewer.vue
      pages/
        Login.vue
        Dashboard.vue
        tasks/
          TaskList.vue
          TaskFormDrawer.vue
          RunDetail.vue
        results/
          ResultList.vue
          ResultDetail.vue
        system/
          UserManagement.vue
          WhitelistManagement.vue
          AuditLogs.vue
```

## 5. 环境变量

`.env.example` 至少包含：

```text
APP_ENV=development
APP_NAME=STRIX Web
API_PREFIX=/api

DATABASE_URL=mysql+pymysql://strix_user:change_me@your-mysql-host:3306/strix_web?charset=utf8mb4
REDIS_URL=redis://:change_me@your-redis-host:6379/0

JWT_SECRET=change-me
JWT_EXPIRE_MINUTES=1440

STRIX_BIN=strix
STRIX_BASE_WORKDIR=./storage/runs
STRIX_DEFAULT_TIMEOUT_SECONDS=7200
STRIX_EVENT_POLL_INTERVAL_MS=500
STRIX_MAX_CONCURRENT_RUNS=2

RUNNER_MODE=in_process
RUNNER_NODE_ID=local-dev
TASK_QUEUE_BACKEND=in_memory
LOCK_BACKEND=redis
EVENT_BUS_BACKEND=redis

ARTIFACT_RETENTION_DAYS=30
LOG_LEVEL=INFO
```

## 6. 数据库设计

数据库固定为 MySQL 8.0+，字符集使用 `utf8mb4`，存储引擎使用 InnoDB。UUID 由后端应用生成，数据库字段使用 `CHAR(36)`。不要依赖 PostgreSQL 的 `UUID`、`JSONB`、`CREATE TYPE` 或 `gen_random_uuid()`。

SQLAlchemy 建议：

- UUID 字段在 Python 中使用 `uuid.uuid4()` 生成字符串。
- 枚举字段可以用 SQLAlchemy `Enum`，也可以用 `String` + 应用层校验。为了 MySQL 迁移清晰，DDL 中使用 MySQL `ENUM`。
- JSON 字段使用 MySQL `JSON` 类型，应用层写入 `{}`，不要依赖 JSON 默认值。
- 时间字段统一使用 `DATETIME(6)`，应用层按 UTC 或统一时区写入，前端展示为 `YYYY-MM-DD HH:mm:ss`。

建库建议：

```sql
CREATE DATABASE IF NOT EXISTS strix_web
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

### 6.1 users

```sql
CREATE TABLE users (
  id CHAR(36) PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  account VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
  department VARCHAR(128),
  status ENUM('enabled', 'disabled') NOT NULL DEFAULT 'enabled',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  last_login_at DATETIME(6),
  INDEX idx_users_role (role),
  INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

关系：

- `users.id` 被 `tasks.created_by`、`task_runs.created_by`、`whitelists.created_by`、`audit_logs.actor_id` 引用。

### 6.2 tasks

```sql
CREATE TABLE tasks (
  id CHAR(36) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  target TEXT NOT NULL,
  target_normalized VARCHAR(512),
  scan_mode ENUM('quick', 'standard', 'deep') NOT NULL,
  interactive TINYINT(1) NOT NULL DEFAULT 0,
  instruction TEXT,
  status ENUM('not_started', 'running', 'completed', 'failed', 'stopped') NOT NULL DEFAULT 'not_started',
  risk_level ENUM('unknown', 'none', 'low', 'medium', 'high') NOT NULL DEFAULT 'unknown',
  created_by CHAR(36) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6),
  CONSTRAINT fk_tasks_created_by FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_tasks_created_by (created_by),
  INDEX idx_tasks_status (status),
  INDEX idx_tasks_risk_level (risk_level),
  INDEX idx_tasks_created_at (created_at),
  INDEX idx_tasks_deleted_at (deleted_at),
  INDEX idx_tasks_target_normalized (target_normalized)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

说明：

- `tasks` 是任务配置，不是一条运行记录。
- 删除使用软删除。
- `target_normalized` 用于白名单匹配，例如域名小写、URL 去默认端口。

### 6.3 task_runs

```sql
CREATE TABLE task_runs (
  id CHAR(36) PRIMARY KEY,
  task_id CHAR(36) NOT NULL,
  run_no INT NOT NULL,
  scan_mode ENUM('quick', 'standard', 'deep') NOT NULL,
  interactive TINYINT(1) NOT NULL DEFAULT 0,
  status ENUM('queued', 'running', 'stopping', 'completed', 'failed', 'stopped') NOT NULL DEFAULT 'queued',
  pid INT,
  runner_node_id VARCHAR(128),
  exit_code INT,
  run_dir VARCHAR(1024) NOT NULL,
  strix_run_dir VARCHAR(1024),
  started_at DATETIME(6),
  ended_at DATETIME(6),
  error_message TEXT,
  created_by CHAR(36) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_task_runs_task_id FOREIGN KEY (task_id) REFERENCES tasks(id),
  CONSTRAINT fk_task_runs_created_by FOREIGN KEY (created_by) REFERENCES users(id),
  UNIQUE KEY uq_task_runs_task_run_no (task_id, run_no),
  INDEX idx_task_runs_task_id (task_id),
  INDEX idx_task_runs_status (status),
  INDEX idx_task_runs_created_at (created_at),
  INDEX idx_task_runs_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

关系：

- 一个 task 可以有多个 task_run。
- 一个 task_run 最多生成一个 result。
- task_run 下可以有多个 run_events 和 artifacts。

### 6.4 run_events

```sql
CREATE TABLE run_events (
  id CHAR(36) PRIMARY KEY,
  run_id CHAR(36) NOT NULL,
  seq BIGINT NOT NULL,
  event_type VARCHAR(128) NOT NULL,
  event_time DATETIME(6),
  payload_json JSON NOT NULL,
  source_file VARCHAR(1024),
  source_offset BIGINT,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_run_events_run_id FOREIGN KEY (run_id) REFERENCES task_runs(id) ON DELETE CASCADE,
  UNIQUE KEY uq_run_events_run_seq (run_id, seq),
  INDEX idx_run_events_run_seq (run_id, seq),
  INDEX idx_run_events_type (event_type),
  INDEX idx_run_events_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

说明：

- 保存关键结构化事件，支持 WebSocket 断线后补拉。
- 不要求所有原始事件都入库，但 MVP 可以先全部入库。
- `payload_json` 由应用层写入 `{}` 或实际事件内容。

### 6.5 results

```sql
CREATE TABLE results (
  id CHAR(36) PRIMARY KEY,
  task_id CHAR(36) NOT NULL,
  run_id CHAR(36) NOT NULL UNIQUE,
  project_name VARCHAR(128) NOT NULL,
  target TEXT NOT NULL,
  scan_mode ENUM('quick', 'standard', 'deep') NOT NULL,
  interactive TINYINT(1) NOT NULL DEFAULT 0,
  status ENUM('completed', 'failed', 'stopped', 'parse_failed') NOT NULL,
  risk_level ENUM('unknown', 'none', 'low', 'medium', 'high') NOT NULL DEFAULT 'unknown',
  vulnerability_count INT NOT NULL DEFAULT 0,
  artifact_dir VARCHAR(1024),
  summary TEXT,
  parse_error TEXT,
  started_at DATETIME(6),
  ended_at DATETIME(6),
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_results_task_id FOREIGN KEY (task_id) REFERENCES tasks(id),
  CONSTRAINT fk_results_run_id FOREIGN KEY (run_id) REFERENCES task_runs(id),
  INDEX idx_results_task_id (task_id),
  INDEX idx_results_status (status),
  INDEX idx_results_risk_level (risk_level),
  INDEX idx_results_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.6 vulnerabilities

```sql
CREATE TABLE vulnerabilities (
  id CHAR(36) PRIMARY KEY,
  result_id CHAR(36) NOT NULL,
  ordinal INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  severity ENUM('unknown', 'none', 'low', 'medium', 'high') NOT NULL DEFAULT 'unknown',
  vuln_type VARCHAR(128),
  affected_target TEXT,
  verified TINYINT(1) NOT NULL DEFAULT 0,
  summary TEXT,
  markdown_artifact_id CHAR(36),
  raw_json JSON,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_vulns_result_id FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE,
  UNIQUE KEY uq_vulns_result_ordinal (result_id, ordinal),
  INDEX idx_vulns_result_id (result_id),
  INDEX idx_vulns_severity (severity),
  INDEX idx_vulns_verified (verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

说明：

- `markdown_artifact_id` 在创建 `artifacts` 后再补外键。
- `raw_json` 由应用层写入原始漏洞信息，可为空。

### 6.7 artifacts

```sql
CREATE TABLE artifacts (
  id CHAR(36) PRIMARY KEY,
  run_id CHAR(36) NOT NULL,
  result_id CHAR(36),
  vulnerability_id CHAR(36),
  artifact_type ENUM('events_jsonl', 'markdown', 'terminal_raw', 'runner_log', 'report', 'other') NOT NULL,
  relative_path VARCHAR(1024) NOT NULL,
  file_name VARCHAR(255),
  content_type VARCHAR(128),
  size_bytes BIGINT,
  sha256 VARCHAR(64),
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_artifacts_run_id FOREIGN KEY (run_id) REFERENCES task_runs(id) ON DELETE CASCADE,
  CONSTRAINT fk_artifacts_result_id FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE,
  CONSTRAINT fk_artifacts_vuln_id FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities(id) ON DELETE SET NULL,
  INDEX idx_artifacts_run_id (run_id),
  INDEX idx_artifacts_result_id (result_id),
  INDEX idx_artifacts_vuln_id (vulnerability_id),
  INDEX idx_artifacts_type (artifact_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE vulnerabilities
  ADD CONSTRAINT fk_vulns_markdown_artifact
  FOREIGN KEY (markdown_artifact_id)
  REFERENCES artifacts(id)
  ON DELETE SET NULL;
```

### 6.8 whitelists

```sql
CREATE TABLE whitelists (
  id CHAR(36) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  target_type ENUM('url', 'domain', 'ip', 'repo') NOT NULL,
  target_value TEXT NOT NULL,
  target_normalized VARCHAR(512) NOT NULL,
  project VARCHAR(128),
  status ENUM('enabled', 'disabled') NOT NULL DEFAULT 'enabled',
  created_by CHAR(36) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_whitelists_created_by FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_whitelists_type (target_type),
  INDEX idx_whitelists_status (status),
  INDEX idx_whitelists_target_normalized (target_normalized)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

执行任务前必须用启用状态的白名单匹配 `tasks.target_normalized`。

### 6.9 audit_logs

```sql
CREATE TABLE audit_logs (
  id CHAR(36) PRIMARY KEY,
  actor_id CHAR(36),
  actor_account VARCHAR(64),
  actor_role ENUM('admin', 'user'),
  action VARCHAR(64) NOT NULL,
  object_type VARCHAR(64),
  object_id CHAR(36),
  request_ip VARCHAR(64),
  result ENUM('success', 'failed') NOT NULL,
  remark TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_audit_logs_actor_id FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_audit_logs_actor_id (actor_id),
  INDEX idx_audit_logs_action (action),
  INDEX idx_audit_logs_result (result),
  INDEX idx_audit_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

审计 action 建议枚举值：

```text
login
logout
create_task
update_task
delete_task
execute_task
stop_task
view_result
download_artifact
create_whitelist
update_whitelist
delete_whitelist
enable_whitelist
disable_whitelist
create_user
update_user
delete_user
enable_user
disable_user
reset_password
```

## 7. 状态机

### 7.1 task_status

```text
not_started  未开始
running      扫描中
completed    扫描完成
failed       扫描失败
stopped      已结束
```

允许流转：

```text
not_started -> running
failed -> running
stopped -> running
running -> completed
running -> failed
running -> stopped
```

禁止：

- `running` 时编辑核心字段。
- `running` 时删除任务。
- `completed` 后修改目标地址、扫描模式、是否交互等核心字段。

### 7.2 run_status

```text
queued -> running -> completed
queued -> running -> failed
queued -> running -> stopping -> stopped
```

`tasks.status` 保存最新运行状态，用于列表展示。真实历史以 `task_runs` 为准。

## 8. REST API 规范

### 8.1 通用返回格式

成功：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

失败：

```json
{
  "code": 40001,
  "message": "账号或密码错误",
  "data": null
}
```

分页：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

### 8.2 Auth

#### POST /api/auth/login

请求：

```json
{
  "account": "admin",
  "password": "admin123",
  "role": "admin"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "token": "jwt-token",
    "user": {
      "id": "uuid",
      "username": "管理员",
      "account": "admin",
      "role": "admin"
    }
  }
}
```

#### GET /api/auth/me

返回当前用户信息。

#### POST /api/auth/logout

写审计日志。JWT 无状态时可仅前端清理 token。

### 8.3 Dashboard

#### GET /api/dashboard/summary

响应：

```json
{
  "activeProjects7d": 12,
  "totalAssetsScanned": 326,
  "highRiskVulns30d": 18
}
```

#### GET /api/dashboard/status-distribution

响应：

```json
[
  { "status": "not_started", "label": "未开始", "count": 5 },
  { "status": "running", "label": "扫描中", "count": 2 }
]
```

#### GET /api/dashboard/recent-scans

查询参数：

```text
limit=10
```

响应字段：

- `taskId`
- `taskName`
- `target`
- `creator`
- `createdAt`
- `scanStatus`
- `riskLevel`

### 8.4 Tasks

#### GET /api/tasks

查询参数：

```text
page
pageSize
name
target
scanMode
interactive
status
riskLevel
createdBy
createdAtStart
createdAtEnd
```

响应 item：

```json
{
  "id": "uuid",
  "name": "example scan",
  "target": "https://example.com",
  "scanMode": "standard",
  "interactive": false,
  "createdBy": "uuid",
  "creatorName": "admin",
  "createdAt": "2026-05-19 16:00:00",
  "status": "not_started",
  "riskLevel": "unknown"
}
```

#### POST /api/tasks

请求：

```json
{
  "name": "example scan",
  "target": "https://example.com",
  "scanMode": "standard",
  "interactive": false,
  "instruction": "Focus on IDOR and XSS"
}
```

规则：

- 只保存，不执行。
- 创建后状态为 `not_started`。
- 任务创建时不强制白名单，但可提示。

#### GET /api/tasks/{taskId}

返回任务详情。

#### PUT /api/tasks/{taskId}

只允许未开始任务修改核心字段。扫描中禁止修改。

#### DELETE /api/tasks/{taskId}

软删除。扫描中禁止删除。

#### POST /api/tasks/{taskId}/execute

请求：

```json
{
  "force": false
}
```

规则：

- 必须登录。
- 必须校验任务存在且未删除。
- 必须校验任务状态允许执行。
- 必须校验白名单。
- 创建 `task_runs`。
- 返回 `runId`。
- 不要在 HTTP 请求里同步等待扫描完成。

响应：

```json
{
  "runId": "uuid",
  "status": "queued"
}
```

#### POST /api/tasks/{taskId}/stop

请求：

```json
{
  "runId": "uuid"
}
```

规则：

- 只能停止 running/stopping 的 run。
- API 调用 Runner 停止进程。
- 状态最终变为 stopped 或 failed。

### 8.5 Runs

#### GET /api/tasks/{taskId}/runs

返回该任务历史运行。

#### GET /api/runs/{runId}

返回运行详情。

#### GET /api/runs/{runId}/events

查询参数：

```text
afterSeq=0
limit=200
```

用于 WebSocket 断线后补拉历史事件。

#### GET /api/runs/{runId}/artifacts

返回当前 run 的 artifact 列表。

### 8.6 Results

#### GET /api/results

查询参数：

```text
page
pageSize
projectName
status
riskLevel
createdBy
startedAtStart
startedAtEnd
sortBy=startedAt
sortOrder=desc
```

响应 item：

```json
{
  "id": "uuid",
  "taskId": "uuid",
  "runId": "uuid",
  "projectName": "example scan",
  "target": "https://example.com",
  "startedAt": "2026-05-19 16:00:00",
  "endedAt": "2026-05-19 16:30:00",
  "status": "completed",
  "riskLevel": "high",
  "vulnerabilityCount": 3
}
```

#### GET /api/results/{resultId}

返回结果基础信息。

#### GET /api/results/{resultId}/vulnerabilities

返回漏洞列表。

#### GET /api/vulnerabilities/{vulnId}/markdown

响应：

```json
{
  "vulnId": "uuid",
  "title": "Stored XSS",
  "markdown": "# Stored XSS\n\n..."
}
```

规则：

- 后端读取 Markdown artifact。
- 校验文件位于 artifact 根目录。
- 前端渲染前使用 DOMPurify 清理 HTML。

### 8.7 Users

仅 admin。

- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/{userId}`
- `DELETE /api/users/{userId}`
- `POST /api/users/{userId}/enable`
- `POST /api/users/{userId}/disable`
- `POST /api/users/{userId}/reset-password`

### 8.8 Whitelists

仅 admin 管理，普通用户只在执行任务时被动校验。

- `GET /api/whitelists`
- `POST /api/whitelists`
- `PUT /api/whitelists/{id}`
- `DELETE /api/whitelists/{id}`
- `POST /api/whitelists/{id}/enable`
- `POST /api/whitelists/{id}/disable`

白名单匹配规则：

- URL：协议、域名、端口、路径规范化后匹配。
- domain：目标 URL 的 hostname 命中域名或子域名。
- IP：目标 host 是该 IP。
- repo：仓库地址规范化后匹配。

#### POST /api/whitelists/check

可选接口，开发调试用。

请求：

```json
{
  "target": "https://example.com"
}
```

响应：

```json
{
  "allowed": true,
  "matchedWhitelistId": "uuid"
}
```

### 8.9 Audit Logs

仅 admin。

#### GET /api/audit-logs

查询参数：

```text
page
pageSize
actor
action
result
createdAtStart
createdAtEnd
```

默认按 `created_at desc`。

## 9. WebSocket 协议

### 9.1 鉴权

连接时必须校验 JWT。

推荐：

```text
ws://host/ws/runs/{runId}/events?token=xxx
ws://host/ws/runs/{runId}/terminal?token=xxx
```

或使用 Sec-WebSocket-Protocol 携带 token。

后端必须检查当前用户是否有权限访问该 run。

### 9.2 结构化事件通道

路径：

```text
/ws/runs/{runId}/events
```

服务端发送 JSON：

```json
{
  "type": "event",
  "runId": "uuid",
  "seq": 12,
  "eventType": "tool_call",
  "payload": {},
  "timestamp": "2026-05-19 16:30:00"
}
```

状态变化：

```json
{
  "type": "status",
  "runId": "uuid",
  "taskId": "uuid",
  "runStatus": "completed",
  "taskStatus": "completed",
  "timestamp": "2026-05-19 16:30:00"
}
```

错误：

```json
{
  "type": "error",
  "runId": "uuid",
  "message": "events.jsonl not found yet"
}
```

前端断线重连后，先调用：

```text
GET /api/runs/{runId}/events?afterSeq=lastSeq
```

再重新连接 WebSocket。

### 9.3 终端通道

路径：

```text
/ws/runs/{runId}/terminal
```

服务端到前端：

- 使用 binary frame。
- 内容是 PTY 原始 bytes。
- 前端直接 `term.write(new Uint8Array(event.data))`。

前端到服务端：

输入：

```json
{
  "type": "input",
  "data": "..."
}
```

resize：

```json
{
  "type": "resize",
  "cols": 120,
  "rows": 36
}
```

ping：

```json
{
  "type": "ping"
}
```

规则：

- xterm.js 负责渲染 ANSI，不要清洗控制码。
- 后端读取 PTY 使用 bytes，不要按行读取。
- 浏览器 resize 后必须同步 PTY window size。
- 终端断线不能自动停止 STRIX。
- 是否允许多人同时旁观或输入必须可配置。MVP 建议只允许创建者输入，其他人只读或禁止进入。

## 10. STRIX Runner 设计

### 10.1 非交互模式执行流程

```text
POST /api/tasks/{id}/execute
  -> Auth
  -> 状态校验
  -> 白名单校验
  -> 创建 task_run(status=queued)
  -> Runner 领取
  -> 创建 run_dir
  -> subprocess.Popen(args, cwd=run_dir)
  -> status=running
  -> 发现 strix_runs/<strix_run_id>/events.jsonl
  -> tail events.jsonl
  -> 保存 run_events
  -> 通过 EventBus 推送
  -> 进程结束
  -> 收尾读取 events.jsonl
  -> result_parser 解析结果
  -> 创建 results/vulnerabilities/artifacts
  -> 更新 task/task_run 状态
```

### 10.2 交互模式执行流程

```text
POST /api/tasks/{id}/execute
  -> task.interactive=true
  -> 创建 task_run
  -> Runner 创建 PTY
  -> fork/exec STRIX
  -> /ws/runs/{runId}/terminal 附着 PTY
  -> 保存 terminal.raw
  -> 用户输入写回 PTY
  -> resize 同步 PTY
  -> 进程退出后更新状态
```

### 10.3 fake STRIX

必须先实现 fake STRIX，避免开发依赖真实工具。

fake 非交互行为：

- 启动后创建 `strix_runs/fake_<timestamp>/events.jsonl`。
- 每 1 秒写一行 JSON。
- 最后生成 `artifacts/vuln-001.md`。
- 退出码为 0。

fake 失败行为：

- 参数 `--fail` 时写错误日志后退出码 1。

fake 交互行为：

- 输出 ANSI 清屏、移动光标、状态刷新。
- 响应键盘输入。
- 可用来验证 xterm.js。

## 11. 结果解析规则

结果来源优先级：

1. STRIX 明确生成的结构化结果文件。
2. `events.jsonl` 中的漏洞或报告事件。
3. Markdown 报告文件。
4. terminal raw 仅用于排错，不作为标准结果来源。

解析输出统一转换为：

```json
{
  "title": "Stored XSS",
  "severity": "high",
  "vulnType": "XSS",
  "affectedTarget": "https://example.com/comment",
  "verified": true,
  "summary": "The comment field is vulnerable...",
  "markdownPath": "artifacts/vuln-001.md",
  "raw": {}
}
```

风险等级计算：

```text
有 high -> high
否则有 medium -> medium
否则有 low -> low
否则漏洞数为 0 -> none
否则 unknown
```

## 12. 前端页面要求

### 12.1 登录页

- 系统名：AI 渗透测试平台。
- 账号、密码、角色。
- 管理端/用户端选择。
- Enter 登录。
- 登录按钮 loading。
- 登录失败显示原因。

### 12.2 主布局

- 左侧菜单默认 1/5 宽。
- 可折叠，只显示图标。
- 右侧内容自适应。
- 顶部显示当前用户、角色、退出登录。
- 当前菜单高亮。
- 用户端不显示系统管理。

### 12.3 首页仪表盘

- 活跃项目数。
- 总资产扫描数量。
- 高危漏洞总数。
- 项目状态环形图。
- 最近扫描记录。

### 12.4 任务管理

- 筛选区。
- 添加任务按钮。
- 任务列表。
- 新建/编辑抽屉。
- 执行、结束、修改、删除按钮。
- 二次确认。
- 状态标签。
- 风险标签。

### 12.5 运行详情

非交互：

- 运行状态。
- 实时事件列表。
- runner 日志。
- artifact 列表。

交互：

- xterm.js 终端。
- resize 自动同步。
- 停止按钮。

### 12.6 结果列表

- 项目名称。
- 扫描时间。
- 结束时间。
- 状态。
- 风险等级。
- 漏洞数量。
- 详情按钮。

### 12.7 结果详情

- 顶部项目基础信息。
- 漏洞表格。
- 点击详情展开 Markdown。
- 支持多个漏洞同时展开。
- Markdown 必须净化 HTML。

### 12.8 系统管理

- 用户管理。
- 白名单管理。
- 审计日志。

## 13. 后端服务类设计

### 13.1 AuthService

职责：

- 登录校验。
- 密码哈希。
- JWT 生成。
- 当前用户解析。

### 13.2 TaskService

职责：

- 任务 CRUD。
- 状态校验。
- 执行前业务校验。

### 13.3 WhitelistService

职责：

- 白名单 CRUD。
- 目标规范化。
- 执行前匹配。

### 13.4 RunService

职责：

- 创建 task_run。
- 调用 Runner。
- 停止 run。
- 查询 run。

### 13.5 StrixRunner

职责：

- 启动 STRIX。
- 监控进程。
- 写状态。
- 推送事件。
- 停止进程。

### 13.6 EventTailer

职责：

- 发现 `events.jsonl`。
- 处理半行 JSON。
- 记录 offset。
- 生成递增 seq。

### 13.7 TerminalSession

职责：

- 创建 PTY。
- 读写 PTY。
- resize。
- 保存 `terminal.raw`。

### 13.8 ResultParser

职责：

- 查找 artifact。
- 解析漏洞。
- 生成 result 和 vulnerabilities。

### 13.9 AuditService

职责：

- 所有关键操作写审计日志。
- 不影响主流程，审计失败要记录后端日志。

## 14. 权限规则

admin：

- 所有页面。
- 所有任务。
- 用户管理。
- 白名单管理。
- 审计日志。

user：

- 首页。
- 自己创建的任务。
- 自己任务的运行和结果。
- 不可访问系统管理。

后端必须强制校验权限。前端隐藏菜单不等于权限控制。

## 15. 错误码建议

```text
0       ok
40000   bad_request
40001   invalid_credentials
40002   role_not_allowed
40100   unauthorized
40300   forbidden
40400   not_found
40900   conflict
40901   task_status_not_allowed
40902   whitelist_not_matched
50000   internal_error
50001   strix_start_failed
50002   strix_stop_failed
50003   result_parse_failed
```

## 16. 测试要求

后端至少测试：

- 登录成功/失败。
- 角色权限。
- 任务 CRUD。
- 状态机。
- 白名单匹配。
- 执行任务创建 run。
- fake STRIX 非交互运行。
- event tailer 半行 JSON。
- 结果解析。
- Markdown 路径安全。
- 审计日志写入。

前端至少人工验收：

- 登录。
- 创建任务。
- 编辑任务。
- 执行任务。
- 实时事件展示。
- 停止任务。
- 查看结果。
- 展开 Markdown。
- 用户端无法进入系统管理。

## 17. Cursor 分阶段执行提示词

以下提示词建议逐段复制给 Cursor。每段完成后先运行项目和测试，再进入下一段。

### 阶段 0：创建项目骨架

提示词：

```text
你是资深全栈工程师。请根据当前文档创建 STRIX Web 平台的 monorepo 项目骨架。

要求：
1. 从空目录初始化 monorepo：创建 backend 和 frontend 两个目录。
2. 后端搭建 FastAPI 工程脚手架，接入 SQLAlchemy 2.x、Alembic、Pydantic Settings、PyMySQL、pytest。
3. 前端使用 Vite 初始化 Vue 3 + TypeScript 工程，接入 Element Plus、Pinia、Vue Router。
4. 不创建 docker-compose.yml。本项目直接连接用户已有的云 MySQL 和云 Redis。
5. 创建 .env.example，使用 mysql+pymysql 的 DATABASE_URL 和云 Redis 的 REDIS_URL。
6. 按文档中的目录结构创建文件。
7. 后端实现 /api/health。
8. 后端创建数据库连接配置，但本阶段不要创建业务表。
9. 前端实现基础空页面并能启动。
10. 不要实现业务功能，先保证前后端工程可启动。

完成后请运行后端测试或最小启动检查，并告诉我启动命令。
```

验收：

- `backend` 可启动。
- `frontend` 可启动。
- `.env.example` 中使用 MySQL 和 Redis 云服务连接配置。
- `/api/health` 返回正常。
- 前端 Vite 首页可访问。

### 阶段 1：数据库模型和迁移

提示词：

```text
请根据文档第 6 节实现数据库模型和 Alembic 迁移。

要求：
1. 实现 users、tasks、task_runs、run_events、results、vulnerabilities、artifacts、whitelists、audit_logs。
2. 使用应用层生成的 UUID 字符串作为主键，数据库字段为 CHAR(36)。
3. 使用 MySQL 8.0 兼容的枚举、JSON、DATETIME(6) 和外键。
4. 实现必要索引、唯一约束和外键。
5. 创建 seed 脚本，初始化 admin 用户。
6. 不要实现页面和复杂业务。
7. 添加基础模型测试，验证表关系可以正常创建。

完成后运行迁移和测试。
```

验收：

- 数据库迁移成功。
- admin 用户可初始化。
- 表关系正确。

### 阶段 2：认证、权限、主布局

提示词：

```text
请实现认证、角色权限和前端主布局。

后端：
1. POST /api/auth/login
2. GET /api/auth/me
3. POST /api/auth/logout
4. JWT 鉴权依赖
5. admin/user 角色权限依赖
6. 登录和失败写审计日志

前端：
1. 登录页，包含账号、密码、角色选择。
2. 登录后保存 token。
3. Vue Router 路由守卫。
4. AdminLayout，左侧菜单可折叠，顶部显示用户和角色。
5. 用户端不显示系统管理。

完成后用 seed admin 账号验证登录。
```

验收：

- 管理端登录成功。
- 用户端无法访问 admin 路由。
- 刷新页面后保持登录态。

### 阶段 3：任务 CRUD 和白名单

提示词：

```text
请实现任务管理和白名单管理。

后端：
1. 实现 tasks CRUD 接口。
2. 实现 whitelists CRUD 接口。
3. 任务创建只保存，不执行。
4. 任务删除使用软删除。
5. 扫描中任务禁止编辑和删除。
6. 实现 WhitelistService，包含目标规范化和执行前匹配方法。
7. 所有关键操作写审计日志。

前端：
1. 任务管理页：筛选、分页、新建、编辑、删除。
2. 白名单管理页：筛选、分页、新建、编辑、删除、启用、禁用。
3. 状态和风险等级使用标签展示。
4. 删除操作二次确认。

暂时不要真正执行 STRIX。
```

验收：

- 可以创建任务。
- 可以创建白名单。
- 删除和编辑规则正确。

### 阶段 4：fake STRIX、Runner、非交互执行、WebSocket 事件

提示词：

```text
请实现 Runner 主链路，但先使用 fake STRIX。

要求：
1. 实现 fake STRIX 非交互脚本，运行时创建 strix_runs/<id>/events.jsonl，并逐行写事件，最后生成 Markdown artifact。
2. 实现 CommandBuilder。
3. 实现 RunService。
4. 实现 ProcessRegistry。
5. 实现 EventTailer，支持半行 JSON、offset、seq。
6. 实现 DistributedLock 抽象，第一版用 Redis 防止同一任务重复执行。
7. 实现 EventBus 抽象，第一版用 Redis Pub/Sub 或 Redis Streams 推送运行事件；如果实现复杂，可先保留 in-memory fallback。
8. 实现 /api/tasks/{taskId}/execute。
9. 实现 /api/tasks/{taskId}/stop。
10. 实现 /api/runs/{runId} 和 /api/runs/{runId}/events。
11. 实现 /ws/runs/{runId}/events。
12. 执行前必须校验白名单。
13. 状态流转必须正确。

前端：
1. 任务列表添加执行、结束按钮。
2. 新增运行详情页。
3. 非交互任务运行时显示实时事件。
4. WebSocket 断开后可通过 REST 补拉事件。

暂时不要接真实 STRIX，先保证 fake STRIX 全链路稳定。
```

验收：

- 点击执行后任务变为扫描中。
- 前端实时看到事件。
- fake STRIX 结束后任务变为扫描完成。
- 可以停止任务。

### 阶段 5：结果解析和结果页面

提示词：

```text
请实现结果解析和结果展示。

后端：
1. 实现 ResultParser，解析 fake STRIX 生成的 Markdown 和事件。
2. 进程结束后创建 results、vulnerabilities、artifacts。
3. 实现 GET /api/results。
4. 实现 GET /api/results/{resultId}。
5. 实现 GET /api/results/{resultId}/vulnerabilities。
6. 实现 GET /api/vulnerabilities/{vulnId}/markdown。
7. 实现 Markdown 文件路径安全校验。
8. 计算项目风险等级并更新 task.risk_level。

前端：
1. 结果列表页。
2. 结果详情页。
3. 漏洞表格。
4. 点击详情展开 Markdown。
5. Markdown 使用 markdown-it 渲染并使用 DOMPurify 净化。
```

验收：

- fake STRIX 完成后自动出现结果记录。
- 可查看漏洞列表。
- 可展开 Markdown。

### 阶段 6：仪表盘和审计日志

提示词：

```text
请实现首页仪表盘和审计日志基础能力。

后端：
1. GET /api/dashboard/summary
2. GET /api/dashboard/status-distribution
3. GET /api/dashboard/recent-scans
4. GET /api/audit-logs
5. 统计口径按文档实现。

前端：
1. 首页统计卡片。
2. 项目状态环形图。
3. 最近扫描记录。
4. 审计日志列表和筛选。
```

验收：

- 首页数据来自真实数据库。
- 审计日志按时间倒序。

### 阶段 7：用户管理

提示词：

```text
请实现系统管理中的用户管理。

要求：
1. 仅 admin 可访问。
2. 用户列表分页。
3. 新增用户。
4. 编辑用户。
5. 启用/禁用用户。
6. 删除用户。
7. 重置密码。
8. 所有操作写审计日志。
9. 禁止普通用户访问相关接口和页面。
```

验收：

- admin 可管理用户。
- user 不能访问用户管理。

### 阶段 8：接入真实 STRIX 非交互

提示词：

```text
请把 Runner 从 fake STRIX 切换为可配置的真实 STRIX。

要求：
1. STRIX_BIN 从环境变量读取。
2. 保留 fake STRIX 模式，便于测试。
3. CommandBuilder 根据 task.scan_mode、task.target、task.instruction、task.interactive 构造参数数组。
4. 非交互任务加 -n。
5. 启动进程时设置 cwd 为 run_dir。
6. 自动发现 run_dir 下的 strix_runs/*/events.jsonl。
7. 真实 STRIX 没有及时产生日志时，不要立刻判失败，只显示 waiting_for_events。
8. 进程退出后做最终结果解析。

不要改动前端页面结构。
```

验收：

- fake 模式仍可测试。
- 真实 STRIX 非交互能运行。
- run_dir 固定且可追踪。

### 阶段 9：交互式终端

提示词：

```text
请实现交互式 STRIX 终端能力。

后端：
1. interactive=true 时使用 PTY 启动 STRIX，不加 -n。
2. 实现 TerminalSession。
3. 实现 /ws/runs/{runId}/terminal。
4. 服务端到前端使用 binary frame 发送 PTY 原始 bytes。
5. 前端到服务端支持 input 和 resize JSON 消息。
6. 保存 terminal.raw artifact。
7. resize 时用 ioctl(TIOCSWINSZ) 调整 PTY 大小。
8. WebSocket 断开不能停止进程。

前端：
1. 实现 TerminalPanel，使用 xterm.js。
2. 直接 term.write 原始 bytes。
3. 用户输入通过 WebSocket 发给后端。
4. 使用 fit addon 自动适配大小并发送 resize。

注意：
不要尝试解析 TUI 为漏洞列表。交互模式的目标是浏览器终端镜像。
```

验收：

- 浏览器中可以看到 STRIX TUI。
- 方向键、Enter、Ctrl+C 等输入可用。
- resize 后界面布局正常。

### 阶段 10：生产加固

提示词：

```text
请进行生产加固和文档补全。

要求：
1. 完善 README。
2. 增加部署说明。
3. 增加日志配置。
4. 增加最大并发扫描限制。
5. 增加运行目录清理脚本。
6. 增加后端重启时 running 任务恢复/标记异常逻辑。
7. 增加更多后端测试。
8. 检查所有文件读取是否限制在 artifact 目录。
9. 检查所有 admin API 是否有权限保护。
10. 检查所有命令执行是否禁止 shell=True。
```

验收：

- 项目可按 README 从 0 启动。
- 关键安全点有测试覆盖。

## 18. 给 Cursor 的总提示词

第一次打开空项目时，可以先投喂这个总提示词：

```text
你现在要从 0 开发一个 STRIX Web 封装平台。请完整阅读当前文档，并严格遵守其中的架构决策、数据库设计、API 规范和阶段计划。

最重要的约束：
1. tasks、task_runs、results、vulnerabilities、artifacts 必须分离。
2. 非交互模式使用 events.jsonl/结构化产物作为主链路。
3. 交互模式只用 PTY + WebSocket + xterm.js 做终端镜像，不解析 TUI 字节流。
4. 普通 CRUD 使用 REST，实时事件和终端使用 WebSocket。
5. Redis 在 MVP 可不启用，但必须预留 Queue、Lock、EventBus 抽象。
6. MySQL 是业务事实来源，Redis 只做临时状态、队列、锁或广播。
7. 启动 STRIX 禁止 shell=True，必须参数数组。
8. 任务执行前必须校验白名单。
9. 后端必须强制权限校验，不能只靠前端隐藏页面。
10. 文件 artifact 读取必须做路径安全校验。

请不要一次性实现全部功能。先执行“阶段 0：创建项目骨架”。阶段完成后停止，告诉我改了哪些文件、如何启动、如何验证。
```

## 19. 人类验收清单

每阶段都问 Cursor：

```text
请列出：
1. 本阶段新增/修改的文件。
2. 已实现的接口和页面。
3. 数据库迁移是否运行成功。
4. 如何启动后端和前端。
5. 如何验证本阶段功能。
6. 哪些功能还没做。
7. 是否有临时实现或技术债。
```

如果 Cursor 一次性改太多文件，要求它先停下，运行测试并解释当前状态。

## 20. 最容易跑偏的点

必须提醒 AI：

- 不要把 STRIX TUI 输出用正则解析成漏洞。
- 不要把任务创建和执行混在一起。
- 不要让任务执行阻塞 HTTP 请求。
- 不要把 WebSocket 当成所有 API 的替代品。
- 不要把 Redis 当数据库。
- 不要把服务器绝对路径返回给前端。
- 不要先做漂亮页面再补状态机。
- 不要省略审计日志。
- 不要绕过白名单。
- 不要用 shell 字符串拼命令。

## 21. 推荐 MVP 边界

MVP 必须有：

- 登录。
- 角色权限。
- 主布局。
- 任务 CRUD。
- 白名单 CRUD。
- 非交互执行。
- 实时事件展示。
- 结果解析。
- 结果列表。
- Markdown 漏洞详情。
- 审计日志基础展示。

MVP 可暂缓：

- 真实交互式终端。
- Redis 分布式队列。
- 多后端实例。
- 报告下载。
- 漏洞趋势分析。
- 多目标扫描。
- CI/CD 集成。

但即使暂缓，也必须预留架构位置，不能写死成单机不可拆结构。
