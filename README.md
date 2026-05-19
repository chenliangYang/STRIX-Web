# STRIX Web 平台

基于 FastAPI + Vue 3 的 STRIX Web 封装平台。

## 项目结构

```
strix-web/
├── backend/          # 后端 (Python FastAPI)
├── frontend/         # 前端 (Vue 3 + TypeScript)
├── README.md
└── .env.example
```

## 快速开始

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入 MySQL/Redis 连接信息

# 运行数据库迁移
alembic upgrade head

# 初始化种子数据
python -m app.db.seed

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端访问: http://localhost:8000

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问: http://localhost:3000

## 默认账号

- 管理员: admin / 123456
- 普通用户: user / 123456

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- MySQL 8.0+
- Redis
- Pydantic v2
- JWT Authentication

### 前端
- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- ECharts
- xterm.js
