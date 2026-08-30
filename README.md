# AI 掘金头条

仿今日头条的新闻应用：FastAPI + MySQL + Redis 提供用户、新闻、收藏和浏览历史；Vue 3 前端独立运行。AI 由后端调用 LLM 与 LangGraph：普通对话、自动分流，以及带人工审核的新闻研究 Agent（站内关键词 + Tavily 站外检索）。

接口细节见 `API接口规范文档.md`，后端设计见 `项目后端设计说明文档.md`。

本仓库面向 **本机开发运行**，不是云主机一键部署。

## 环境要求

先安装并启动下面服务，再装 Python / Node 依赖：

- Python 3.11+
- Node.js 18+
- MySQL 8，确认 `3306` 端口在监听
- Redis，确认 `6379` 端口在监听（Windows 可用 Memurai 或 WSL 中的 Redis）

## 1. 克隆与 Python 依赖

```powershell
cd app_toutiao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS：`source .venv/bin/activate`。

## 2. 环境变量

所有本机账号都写在 `.env`，不要改 Python 配置文件。

```powershell
copy .env.example .env
```

至少填写 `MYSQL_PASSWORD`（以及你的 MySQL 用户名、主机）。`LLM_*` 和 `TAVILY_API_KEY` 只有要用 AI 时才需要。

`.env` 已在 `.gitignore` 中，不要提交。

## 3. 导入数据库

`.env` 里的 `MYSQL_DATABASE` 须与脚本一致（默认 `news_app`）。用 **MySQL Workbench** 打开 `database.sql` 执行，或在 PowerShell 中：

```powershell
Get-Content .\database.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
```

不要使用 `mysql < database.sql`：在 PowerShell 里通常无效。

脚本会创建库、表（含 `research_run`）和示例新闻。若库是旧版本、只缺研究任务表，单独执行脚本里 `research_run` 那段 `CREATE TABLE`。

## 4. 启动后端

确认 Redis 已运行。在项目根目录：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs

缺少 MySQL / Redis 环境变量时，进程会报错并提示去填写 `.env`。LangGraph 检查点写在 `data/research_checkpoints.db`（目录已忽略）。

## 5. 启动前端

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（默认 http://localhost:5173）。前端请求 `http://localhost:8000`，CORS 已放行 5173 / 5174。

## 使用说明

- **先注册再登录。** 种子数据只有新闻，没有现成账号。
- 分类、列表、搜索、详情无需登录；发布、收藏、历史和 **全部 AI 接口** 需要登录。
- **不填 LLM / Tavily 时**：新闻浏览、搜索、发布仍可用；打开 `/ai` 或发起研究会失败，这是预期行为。
- 首页搜索与研究 Agent 站内检索共用关键词查询。深度研究先按实体短词搜站内，不足再用 Tavily（近一年）补齐。草稿需人工审核；刷新 `/ai` 会先恢复最近的普通对话，再恢复待审核或最近已完成的报告。明确使用对话模式的问答写入 `ai_chat`；「清空记录」会同时清除对话和研究。
- 对话超时约 60 秒，研究启动与审核约 300 秒。

## 仓库约定

- 密钥和数据库密码只放 `.env`。
- `data/` 为本地检查点，不入库。
