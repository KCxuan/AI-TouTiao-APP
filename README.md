# AI 掘金头条

仿今日头条的新闻应用：浏览、搜索、发布、收藏、浏览历史，以及带人工审核的 AI 新闻研究。

- 试用：安装 Docker 后，配置 `.env` 再 `docker compose up`，浏览器只开一个地址。
- 开发：本机分别启动 FastAPI 和 Vue。下面两套可以并存，互不影响。

接口细节见 `API接口规范文档.md`，更细的后端设计见 `项目后端设计说明文档.md`。

---

## 先选一条路

| 你想做什么 | 用哪条 | 需要事先安装 |
|------------|--------|----------------|
| 打开页面试用、演示给别人 | [一、Docker 一键启动](#一docker-一键启动推荐试用) | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| 改后端 / 前端代码、热更新 | [二、本机开发启动](#二本机开发启动) | Python 3.11+、Node.js 18+、本机 MySQL 8、Redis |

两条路都要先克隆仓库，并准备一份 `.env`（不要提交到 Git）。

```powershell
git clone https://github.com/KCxuan/AI-TouTiao-APP.git
cd AI-TouTiao-APP
copy .env.example .env
```

Linux / macOS：`cp .env.example .env`。

`.env` 里至少改 `MYSQL_PASSWORD`（自己设一个即可；Docker 里它会成为容器 MySQL 的 root 密码）。`MYSQL_HOST` / `REDIS_HOST` 保持示例值就行：本机开发连 `127.0.0.1` / `localhost`；Docker 会在容器内自动改成 `mysql` / `redis`。第一次成功启动后不要改这个密码；改了必须先 `docker compose down -v` 再 `up`，否则 MySQL 对不上旧数据卷。

要用 AI 对话或深度研究，再填写：

```dotenv
LLM_API_KEY=...
LLM_MODEL_ID=...
LLM_BASE_URL=...
TAVILY_API_KEY=...
```

不填这些时，新闻浏览、搜索、注册、发布仍可用；打开「AI 研究」会失败，这是预期行为。

---

## 一、Docker 一键启动（推荐试用）

1. 安装并**启动** Docker Desktop。
2. 按上面复制并填写 `.env`。
3. 在项目根目录执行：

```powershell
docker compose up -d --build
```

第一次会拉镜像、构建前后端，可能需要十几分钟。用 `docker compose ps` 确认 `mysql`、`api` 为 healthy 后再打开浏览器。之后再启动一般只用：

```powershell
docker compose up -d
```

4. 浏览器打开 http://localhost  
   - 80 端口被占用时，在 `.env` 里加上 `WEB_PORT=8080`，再执行一次 `docker compose up -d`，改为打开 http://localhost:8080  
   - 接口文档：http://localhost/docs

5. **先注册一个账号再登录。** 种子数据只有示例新闻，没有现成用户。容器里的库和你本机 MySQL 不是同一套，本机注册过的账号在这里用不了。

常用命令：

```powershell
docker compose logs -f
docker compose down
```

`down` 不要加 `-v`，否则容器里的新闻库和研究记录会被清掉。空数据卷第一次启动时，官方镜像会自动导入 `database.sql`，不必再手动执行 SQL。

需要重新导入种子数据时（启动失败、标题中文乱码、或想清空容器库），先 `docker compose down -v` 再 `up`。只改了 `.env` 里的 AI 密钥时，执行 `docker compose up -d` 即可，不必 `--build`，也不要 `-v`。

Compose **不会占用** 本机 `3306` / `6379`，可以和本机已有的 MySQL、Redis 同时存在。测 Docker 时用 80 端口，测本机开发时用 5173，不要混在一个窗口里对照。

---

## 二、本机开发启动

适合改代码。先自行安装并启动：

- Python 3.11+
- Node.js 18+
- MySQL 8（`3306` 在监听）
- Redis（`6379` 在监听；Windows 可用 Memurai 或 WSL 中的 Redis）

### 1. Python 依赖

```powershell
cd AI-TouTiao-APP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS：`source .venv/bin/activate`。

### 2. 导入数据库

`.env` 里的 `MYSQL_DATABASE` 须与脚本一致（默认 `news_app`）。用 **MySQL Workbench** 打开 `database.sql` 执行，或在 PowerShell 中：

```powershell
Get-Content .\database.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
```

不要使用 `mysql < database.sql`：在 PowerShell 里通常无效。

脚本会创建库、表和示例新闻。若库是旧版本、只缺研究任务表，单独执行脚本里 `research_run` 那段 `CREATE TABLE`。

### 3. 启动后端

确认 Redis 已运行。在项目根目录：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs

缺少 MySQL / Redis 环境变量时，进程会报错并提示去填写 `.env`。

### 4. 启动前端

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（默认 http://127.0.0.1:5173）。前端默认请求 `http://localhost:8000`，CORS 默认放行 5173 / 5174。

---

## 跑起来之后怎么用

- **先注册再登录。** 没有预置账号。
- 分类、列表、搜索、详情无需登录。
- 发布、编辑、删除、收藏、浏览历史、全部 AI 接口需要登录。
- 首页搜索与研究 Agent 的站内检索共用同一套关键词查询。
- 深度研究：先按实体短词搜站内新闻，不足再用 Tavily（近一年）补齐；草稿必须人工审核后才能定稿。
- 进入「AI 研究」会先恢复最近的普通对话，再追加待审核或最近已完成的报告。明确使用对话模式的问答会写入 `ai_chat`；「清空记录」会同时清除对话和研究。
- 前端超时：普通对话约 60 秒，自动模式 / 研究启动 / 审核约 300 秒。

---

## 项目架构

前后端分离。浏览器只调本仓库的 FastAPI，不直连模型供应商。

```
浏览器
  ├─ 本机开发：Vite :5173  ──axios──►  FastAPI :8000
  └─ Docker：  Nginx :80
                 ├─ /        Vue 构建产物
                 └─ /api     FastAPI 容器
                                ├─ MySQL（用户 / 新闻 / 收藏 / 历史 / ai_chat / research_run）
                                ├─ Redis（分类、列表、详情、相关新闻缓存）
                                └─ LLM + Tavily（可选；研究图检查点在 data/）
```

| 层 | 目录 | 做什么 |
|----|------|--------|
| 路由 | `routers/` | HTTP 接口，统一返回 `{code, message, data}` |
| 服务 | `services/` | AI 对话、自动分流、研究任务（路由不直接操作 LangGraph） |
| 数据访问 | `crud/` | 增删改查；新闻缓存的读写和失效也在这里 |
| 模型 / 校验 | `models/`、`schemas/` | SQLAlchemy ORM、Pydantic 请求体 |
| 研究 Agent | `new_research_agent/` | LangGraph：规划 → 检索 → 评估 → 写稿 → 人工审核 → 定稿 |
| 前端 | `frontend/` | Vue 3 + Vite + Vue Router + Pinia + Axios |

认证：登录或注册后拿到 token，请求头使用 `Authorization: Bearer <token>`，有效期 7 天。身份字段（作者、user_id）由服务端从 token 推导，请求体不接收。

研究流程简述：

```
analyze_goal → search_news → assess_evidence
                    ↑ 证据不足且未满 3 轮
                    └── 再搜
充分或达上限 → 写草稿 → 人工审核
  通过 → 定稿（不重写正文）
  修改 / 补查 / 换目标 → 继续同一任务
```

密钥、数据库密码只放 `.env`。LangGraph 检查点在 `data/`（已加入 `.gitignore`）。Compose 只适合本机试用和演示，不是云上生产部署手册。

更完整的表结构、缓存失效矩阵和接口字段，见仓库里的两份 Markdown 文档。
