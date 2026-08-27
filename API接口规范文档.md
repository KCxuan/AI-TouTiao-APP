# 头条新闻 API 接口规范

> 文档版本：1.2
> 更新时间：2026-08-27
> 适用后端：FastAPI

## 概述

本文档描述头条新闻系统当前已经挂载的 HTTP API，包括用户、新闻、收藏、浏览历史，以及 AI 普通对话、深度研究和自动模式。

## 基础地址

```text
http://127.0.0.1:8000
```

使用 `http://localhost:8000` 也可以访问本地服务。FastAPI 自动生成的调试文档位于：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

## 本地启动

启动后端前，在项目根目录复制 `.env.example` 为 `.env`，填写 MySQL / Redis；调用 AI 时再填写 LLM 与 Tavily。完整变量列表见 `.env.example`。`.env` 不应提交到版本控制。

启动示例：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

详细步骤（导入 `database.sql`、PowerShell 注意点、先注册再使用 AI）见仓库根目录 `README.md`。

## 请求约定

- 除 GET、DELETE 查询参数外，请求体均使用 JSON。
- 请求头建议包含 `Content-Type: application/json`。
- 文档中的时间均为 ISO 8601 字符串。
- 字段名以接口示例为准；部分旧业务接口通过 Pydantic alias 对外使用 camelCase，AI 接口使用 snake_case。

## 认证方式

需要认证的接口必须携带登录或注册接口返回的 token。当前后端会按空格拆分请求头并读取第二段，因此必须使用完整的 Bearer 格式：

```http
Authorization: Bearer <token>
```

需要认证的范围：

- 用户信息、资料修改和密码修改；
- 新闻发布、我的发布、新闻编辑和删除；
- 全部收藏与浏览历史接口；
- 全部 AI 接口（对话、自动模式、研究启动、审核、恢复当前任务、清空记录）。

新闻公开查询（分类、列表、搜索、详情）暂不要求登录。

当前 token 有效期为 7 天。注册成功时会生成 token；同一用户重新登录时，服务端会替换原来的 token。项目暂未提供 refresh token 和退出登录接口。

认证相关的当前错误行为：

- 缺少 `Authorization` 请求头：FastAPI 返回 HTTP 422；
- Bearer 格式正确，但 token 无效或过期：返回 HTTP 401；
- 客户端必须使用完整 Bearer 格式，不要只发送裸 token。

## 响应格式

业务接口成功时使用以下统一结构，并返回 HTTP 200：

```json
{
  "code": 200,
  "message": "接口处理结果",
  "data": {}
}
```

`data` 可能是对象、数组或 `null`。业务类 `HTTPException` 通常仍使用同一结构，并将 HTTP 状态码同步写入 `code`：

```json
{
  "code": 404,
  "message": "资源不存在",
  "data": null
}
```

请求字段缺失、类型错误或枚举值非法时，FastAPI 返回 HTTP 422，格式为默认的 `detail` 数组，不经过上述统一包装：

```json
{
  "detail": [
    {
      "type": "validation_error",
      "loc": ["body", "field"],
      "msg": "错误说明",
      "input": null
    }
  ]
}
```

未捕获异常返回 HTTP 500、`code=500`。当前项目处于开发模式，`data` 中可能包含异常详情和 traceback，部署前应关闭详细错误输出。

常见 HTTP 状态码：

| 状态码 | 含义 | 常见场景 |
|--------|------|----------|
| 200 | 请求成功 | 正常读取、创建、更新或删除 |
| 400 | 请求无法完成 | 用户已存在、登录失败、取消不存在的收藏 |
| 401 | 认证失败 | token 无效或已过期 |
| 403 | 无操作权限 | 编辑或删除其他用户发布的新闻；审核不属于自己的研究任务 |
| 404 | 资源不存在 | 新闻或浏览记录不存在 |
| 409 | 资源状态冲突 | 对非待审核的研究任务提交审核 |
| 422 | 请求校验失败 | 缺少字段、类型错误、非法枚举值或缺少必填 Header |
| 500 | 服务器内部错误 | 数据库、模型、搜索或未捕获的运行异常 |

## 接口详情

### 根接口

- **接口地址**：`GET /`
- **请求头**：不需要认证
- **响应**：

```json
{
  "message": "Hello World"
}
```

该接口不使用 `{code, message, data}` 通用包装。

### 用户管理模块

#### 1. 用户注册

- **接口地址**: `POST /api/user/register`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名，3-20 个字符 |
| password | string | 是 | 密码，6-100 个字符 |

- **请求示例**:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "nickname": null,
      "avatar": null,
      "gender": "unknown",
      "bio": "这个人很懒，没有签名"
    }
  }
}
```

#### 2. 用户登录

- **接口地址**: `POST /api/user/login`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名，3-20 个字符 |
| password | string | 是 | 密码，6-100 个字符 |

- **请求示例**:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "nickname": null,
      "avatar": null,
      "gender": "unknown",
      "bio": "这个人很懒，没有签名"
    }
  }
}
```

#### 3. 获取用户信息

- **接口地址**: `GET /api/user/info`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "获取信息成功",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": null,
    "gender": "unknown",
    "bio": "这个人很懒，没有签名"
  }
}
```

#### 4. 更新用户信息

- **接口地址**: `PUT /api/user/update`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像URL |
| gender | string | 否 | 性别 |
| bio | string | 否 | 个人简介 |
| phone | string | 否 | 手机号 |

- **请求示例**:

```json
{
  "bio": "这是我的个人简介"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "更新用户信息成功",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这是我的个人简介"
  }
}
```

#### 5. 修改用户密码

- **接口地址**: `PUT /api/user/password`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| oldPassword | string | 是 | 当前密码 |
| newPassword | string | 是 | 新密码 |

- **请求示例**:

```json
{
  "oldPassword": "current_password",
  "newPassword": "new_password"
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "修改密码成功",
  "data": null
}
```

### 新闻模块

#### 1. 获取新闻分类列表

- **接口地址**: `GET /api/news/categories`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| skip | integer | 否 | 跳过的记录数，默认为0 |
| limit | integer | 否 | 返回的记录数限制，默认为100 |

- **请求示例**:

```
GET /api/news/categories
GET /api/news/categories?skip=0&limit=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "name": "科技",
      "sort_order": 0
    }
  ]
}
```

#### 2. 获取新闻列表

- **接口地址**: `GET /api/news/list`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| categoryId | integer | 是 | 分类ID |
| page | integer | 否 | 页码，默认为1 |
| pageSize | integer | 否 | 每页显示的新闻数量，最大值为100，默认为10 |

- **请求示例**:

```
GET /api/news/list?categoryId=1
GET /api/news/list?categoryId=1&page=2&pageSize=20
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "publish_time": "2023-01-01T00:00:00",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "title": "新闻标题",
        "description": "新闻简介",
        "content": "新闻内容",
        "image": null,
        "author": null,
        "user_id": 1,
        "category_id": 1,
        "views": 0
      }
    ],
    "total": 100,
    "hasMore": true
  }
}
```

#### 2.1 搜索新闻

- **接口地址**: `GET /api/news/search`
- **请求头**: 不需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| q | string | 是 | 搜索关键词，去首尾空格后 1-50 个字符 |
| categoryId | integer | 否 | 分类 ID；不传则全站搜索 |
| page | integer | 否 | 页码，默认为 1 |
| pageSize | integer | 否 | 每页数量，1-100，默认为 10 |

- **请求示例**:

```
GET /api/news/search?q=C919
GET /api/news/search?q=C919&categoryId=1&page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "搜索成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "C919国产大飞机开启东南亚演示飞行",
        "description": "新闻简介",
        "content": "新闻内容",
        "image": null,
        "author": null,
        "user_id": 1,
        "category_id": 1,
        "views": 0
      }
    ],
    "total": 1,
    "hasMore": false,
    "keyword": "C919",
    "categoryId": null
  }
}
```

- **说明**：
  - 匹配 `title` 和 `description` 的整段 LIKE，不搜正文，不走缓存。
  - `%`、`_` 会按字面量转义，不会被当成 SQL 通配符。
  - 标题命中排在简介命中之前，再按发布时间、id 倒序。
  - 首页搜索框与研究 Agent 站内检索共用 `search_news_by_keyword`。Agent 侧使用规划产出的实体短词（如 `C919`），而不是用户整句。

#### 3. 获取新闻详情

- **接口地址**: `GET /api/news/detail`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 新闻ID |

- **请求示例**:

```
GET /api/news/detail?id=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "content": "新闻内容",
    "image": null,
    "author": null,
    "publishTime": "2023-01-01T00:00:00",
    "categoryId": 1,
    "views": 1,
    "relatedNews": []
  }
}
```

- **说明**：
  - 每次成功请求详情接口都会将该新闻的 `views` 增加 1。
  - `relatedNews` 非空时，每一项是完整的新闻 ORM 数据，字段采用 snake_case。

#### 4. 发布新闻

- **接口地址**: `POST /api/news/publish`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 新闻标题，1-255 个字符 |
| description | string | 否 | 新闻简介，最多 500 个字符 |
| content | string | 是 | 新闻内容 |
| image | string | 否 | 封面图片URL，最多 255 个字符 |
| categoryId | integer | 是 | 分类ID，必须为已存在的分类 |

- **请求示例**:

```json
{
  "title": "新闻标题",
  "description": "新闻简介",
  "content": "新闻内容",
  "image": "https://example.com/cover.jpg",
  "categoryId": 1
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "发布新闻成功",
  "data": {
    "id": 101,
    "title": "新闻标题",
    "description": "新闻简介",
    "content": "新闻内容",
    "image": "https://example.com/cover.jpg",
    "author": "example_user",
    "user_id": 1,
    "category_id": 1,
    "views": 0,
    "publish_time": "2023-01-01T00:00:00",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

- **说明**:
  - `author` 由服务端自动填充为当前登录用户的用户名，无需前端传入
  - `views` 默认为 0；`publish_time`、`created_at`、`updated_at` 由服务端自动生成
  - 发布成功后会自动清除该分类的新闻列表缓存和相关新闻缓存，新文章立即在列表中可见
  - 分类不存在时返回 404（Category not found）；未登录或 token 失效返回 401

#### 5. 获取我的发布列表

- **接口地址**: `GET /api/news/mine`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为1 |
| pageSize | integer | 否 | 每页条数，默认为10，最大值为100 |

- **请求示例**:

```
GET /api/news/mine
GET /api/news/mine?page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取新闻列表成功",
  "data": {
    "list": [
      {
        "id": 101,
        "title": "新闻标题",
        "description": "新闻简介",
        "content": "新闻内容",
        "image": null,
        "author": "example_user",
        "user_id": 1,
        "category_id": 1,
        "views": 0,
        "publish_time": "2023-01-01T00:00:00",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

- **说明**:
  - 仅返回当前登录用户发布的新闻（user_id 匹配），按发布时间倒序
  - 存量旧数据（user_id 为 NULL）不属于任何用户，不会出现在任何人的列表中

#### 6. 编辑新闻

- **接口地址**: `PUT /api/news/update`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 新闻ID |
| title | string | 否 | 新闻标题，1-255 个字符 |
| description | string | 否 | 新闻简介，最多 500 个字符 |
| content | string | 否 | 新闻内容 |
| image | string | 否 | 封面图片URL，最多 255 个字符 |
| categoryId | integer | 否 | 分类ID，必须为已存在的分类 |

- **请求示例**:

```json
{
  "id": 101,
  "title": "修改后的新闻标题",
  "categoryId": 2
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "更新新闻成功",
  "data": {
    "id": 101,
    "title": "修改后的新闻标题",
    "description": "新闻简介",
    "content": "新闻内容",
    "image": null,
    "author": "example_user",
    "user_id": 1,
    "category_id": 2,
    "views": 0,
    "publish_time": "2023-01-01T00:00:00",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-02T00:00:00"
  }
}
```

- **说明**:
  - 部分更新：仅更新请求中传入的字段，未传入的字段保持原值
  - 仅允许编辑自己发布的新闻：文章不存在返回 404；非本人文章（含存量无主文章）返回 403
  - `updated_at` 由服务端自动更新
  - 编辑成功后自动清除该新闻的详情缓存、相关分类的列表缓存（跨分类编辑时新旧分类均清除）及全部相关新闻缓存

#### 7. 删除新闻

- **接口地址**: `DELETE /api/news/delete/{news_id}`
- **请求头**: 需要认证
- **路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| news_id | integer | 是 | 新闻ID |

- **请求示例**:

```
DELETE /api/news/delete/101
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "删除新闻成功",
  "data": {
    "id": 101,
    "title": "新闻标题",
    "description": "新闻简介",
    "content": "新闻内容",
    "image": null,
    "author": "example_user",
    "user_id": 1,
    "category_id": 1,
    "views": 0,
    "publish_time": "2023-01-01T00:00:00",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

- **说明**:
  - 仅允许删除自己发布的新闻：文章不存在返回 404；非本人文章（含存量无主文章）返回 403
  - 删除时数据库自动级联清理该新闻对应的收藏记录和浏览历史（外键 ON DELETE CASCADE）
  - 删除成功后自动清除该新闻的详情缓存、原分类的列表缓存及全部相关新闻缓存

### 收藏模块

#### 1. 检查新闻收藏状态

- **接口地址**: `GET /api/favorite/check`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```
GET /api/favorite/check?newsId=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "检查收藏成功",
  "data": {
    "isFavorite": true
  }
}
```

#### 2. 添加收藏

- **接口地址**: `POST /api/favorite/add`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```json
{
  "newsId": 1
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "添加收藏成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "news_id": 1,
    "created_at": "2023-01-01T00:00:00"
  }
}
```

#### 3. 取消收藏

- **接口地址**: `DELETE /api/favorite/remove`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```
DELETE /api/favorite/remove?newsId=1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "删除收藏成功",
  "data": null
}
```

#### 4. 获取收藏列表

- **接口地址**: `GET /api/favorite/list`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为1 |
| pageSize | integer | 否 | 每页条数，默认为10，最大值为100 |

- **请求示例**:

```
GET /api/favorite/list
GET /api/favorite/list?page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取收藏的新闻列表成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "publishTime": "2023-01-01T00:00:00",
        "categoryId": 1,
        "views": 1,
        "favoriteId": 1,
        "favoriteTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 5. 清空所有收藏

- **接口地址**: `DELETE /api/favorite/clear`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "清空全部1条收藏成功",
  "data": null
}
```

### 浏览历史模块

#### 1. 添加浏览记录

- **接口地址**: `POST /api/history/add`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| newsId | integer | 是 | 新闻ID |

- **请求示例**:

```json
{
  "newsId": 1
}
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "添加浏览历史成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "news_id": 1,
    "view_time": "2023-01-01T00:00:00"
  }
}
```

#### 2. 获取浏览历史列表

- **接口地址**: `GET /api/history/list`
- **请求头**: 需要认证
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为1 |
| pageSize | integer | 否 | 每页条数，默认为10，最大值为100 |

- **请求示例**:

```
GET /api/history/list
GET /api/history/list?page=1&pageSize=10
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "获取浏览历史列表成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "publishTime": "2023-01-01T00:00:00",
        "categoryId": 1,
        "views": 1,
        "historyId": 1,
        "viewTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 3. 删除单条浏览记录

- **接口地址**: `DELETE /api/history/delete/{history_id}`
- **请求头**: 需要认证
- **路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| history_id | integer | 是 | 历史记录ID |

- **请求示例**:

```
DELETE /api/history/delete/1
```

- **响应示例**:

```json
{
  "code": 200,
  "message": "删除浏览记录成功",
  "data": null
}
```

#### 4. 清空浏览历史

- **接口地址**: `DELETE /api/history/clear`
- **请求头**: 需要认证
- **响应示例**:

```json
{
  "code": 200,
  "message": "清空历史浏览列表成功,一共1条记录",
  "data": null
}
```

### AI 助手模块

当前 AI 模块提供六个同步接口，**全部需要登录**：

| 功能 | 方法 | 接口地址 | 认证 |
|------|------|----------|------|
| 普通对话 | POST | `/api/ai/chat` | 需要 |
| 自动选择模式 | POST | `/api/ai/auto` | 需要 |
| 发起深度研究 | POST | `/api/ai/research/start` | 需要 |
| 审核研究草稿 | POST | `/api/ai/research/{thread_id}/review` | 需要 |
| 恢复当前研究 | GET | `/api/ai/research/current` | 需要 |
| 清空当前研究 | DELETE | `/api/ai/research/current` | 需要 |

这些接口当前均等待模型或研究流程执行结束后一次性返回 JSON，不使用 SSE 或 WebSocket。普通对话不会搜索新闻。深度研究先按实体关键词检索站内新闻，不足再用 Tavily 补齐，并生成带来源的报告。

前端 `/ai` 路由需要登录；进入页面时调用 `GET /api/ai/research/current` 恢复待审核草稿或最近已完成报告；「清空记录」调用 `DELETE /api/ai/research/current`。

#### 1. 普通 AI 对话

- **接口地址**：`POST /api/ai/chat`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | string | 是 | 本次用户消息，至少 1 个字符 |
| history | array | 否 | 本次消息之前已经完成的短期对话，默认为 `[]` |
| history[].role | string | 是 | 只能是 `user` 或 `assistant` |
| history[].content | string | 是 | 历史消息正文，至少 1 个字符 |

- **请求示例**：

```json
{
  "message": "什么是 LangGraph？",
  "history": [
    {
      "role": "user",
      "content": "什么是 Agent？"
    },
    {
      "role": "assistant",
      "content": "Agent 是能够根据目标采取行动的系统。"
    }
  ]
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "对话成功",
  "data": {
    "answer": "LangGraph 是一个用于构建有状态 Agent 工作流的框架。"
  }
}
```

- **说明**：
  - 后端最多使用 `history` 中最后 20 条消息。
  - `history` 不应重复放入本次 `message`。
  - Chat 模式不会调用新闻搜索工具；涉及实时新闻、多来源对比或可追溯证据时应使用 Research。

#### 2. 发起深度研究

- **接口地址**：`POST /api/ai/research/start`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_input | string | 是 | 新闻研究主题，至少 1 个字符 |

- **请求示例**：

```json
{
  "user_input": "研究最近一周 AI 手机领域的重要新闻"
}
```

- **等待审核响应示例**：

```json
{
  "code": 200,
  "message": "研究报告草稿已生成",
  "data": {
    "thread_id": "950ab24d-0b03-4c15-9ac8-bca4b6f833f9",
    "status": "waiting_review",
    "user_input": "研究最近一周 AI 手机领域的重要新闻",
    "instruction": "请审核新闻研究报告草稿。",
    "draft_report": "# 新闻研究报告\n\n……",
    "final_report": null,
    "search_round": 3,
    "hard_max_search_rounds": 5,
    "allowed_actions": [
      "approve",
      "revise",
      "research_more",
      "change_goal"
    ]
  }
}
```

- **响应字段**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| thread_id | string | 本次 LangGraph 研究任务的标识，后续审核必须原样携带 |
| status | string | `waiting_review` 或 `completed` |
| user_input | string \| null | 本次研究主题 |
| instruction | string \| null | 当前需要用户执行的操作说明 |
| draft_report | string \| null | 等待审核的 Markdown 草稿 |
| final_report | string \| null | 审核通过后的最终 Markdown 报告 |
| search_round | integer \| null | 已完成的搜索轮数 |
| hard_max_search_rounds | integer \| null | 搜索绝对上限，当前默认为 5 |
| allowed_actions | string[] | 当前真正允许提交的审核动作 |

- **说明**：
  - Agent 初始最多自动搜索 3 轮，用户补查后的硬上限为 5 轮。
  - 规划会同时产出站外自然语言查询 `current_query` 和站内实体短词 `internal_keywords`。
  - 每轮最多 5 条来源：先按关键词搜站内（`internal://news/{id}`），不足再以 Tavily（`topic=news`，`time_range=year`）补齐。
  - 同一用户新开研究前，旧的 `waiting_review` 任务会被标为 `abandoned`，不再出现在 `GET /current` 中。
  - 正常启动会执行到人工审核节点后暂停，因此首次返回通常是 `waiting_review`。
  - 客户端应保存 `thread_id` 和完整的 `allowed_actions`，不要自行推测可用操作。

#### 3. 审核并恢复研究

- **接口地址**：`POST /api/ai/research/{thread_id}/review`
- **请求头**：需要认证
- **路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| thread_id | string | 是 | 启动研究接口返回的任务标识 |

- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| action | string | 是 | `approve`、`revise`、`research_more` 或 `change_goal` |
| feedback | string \| null | 否 | 修改意见、补查方向或新的研究目标 |

四种审核动作的实际行为：

| action | feedback 要求 | 后续流程 |
|--------|---------------|----------|
| approve | 不需要，传入也会被忽略 | 将当前草稿直接确认为最终报告 |
| revise | 去除首尾空格后必须非空 | 按修改意见重新生成完整草稿，再次等待审核 |
| research_more | 可选 | 继续搜索；为空时使用默认补查方向 |
| change_goal | 去除首尾空格后必须非空 | 清除旧资料，用新的研究目标重新开始 |

- **修改草稿请求示例**：

```json
{
  "action": "revise",
  "feedback": "减少背景介绍，增加不同厂商的观点对比"
}
```

- **继续等待审核响应示例**：

```json
{
  "code": 200,
  "message": "研究报告草稿已更新",
  "data": {
    "thread_id": "950ab24d-0b03-4c15-9ac8-bca4b6f833f9",
    "status": "waiting_review",
    "instruction": "请审核新闻研究报告草稿。",
    "draft_report": "# 修改后的新闻研究报告\n\n……",
    "final_report": null,
    "search_round": 3,
    "hard_max_search_rounds": 5,
    "allowed_actions": [
      "approve",
      "revise",
      "research_more",
      "change_goal"
    ]
  }
}
```

- **审核通过请求示例**：

```json
{
  "action": "approve",
  "feedback": null
}
```

- **审核通过响应示例**：

```json
{
  "code": 200,
  "message": "研究报告已完成",
  "data": {
    "thread_id": "950ab24d-0b03-4c15-9ac8-bca4b6f833f9",
    "status": "completed",
    "instruction": null,
    "draft_report": null,
    "final_report": "# 最终新闻研究报告\n\n……",
    "search_round": null,
    "hard_max_search_rounds": null,
    "allowed_actions": []
  }
}
```

- **审核循环说明**：
  - `revise`、`research_more` 和 `change_goal` 完成后都会再次返回 `waiting_review`，客户端继续使用同一个 `thread_id` 审核。
  - 当 `search_round >= hard_max_search_rounds` 时，`research_more` 会从 `allowed_actions` 中移除。
  - 即使请求 Schema 允许 `research_more`，客户端也只能提交当前 `allowed_actions` 中存在的动作。
  - `approve` 不会重新生成正文，`final_report` 就是用户刚刚审核通过的草稿。
  - `thread_id` 必须属于当前登录用户，否则返回 HTTP 403。
  - 任务状态不是 `waiting_review` 时提交审核返回 HTTP 409。

#### 4. 获取当前研究

- **接口地址**：`GET /api/ai/research/current`
- **请求头**：需要认证
- **请求参数**：无

- **有可恢复任务时**：`data` 结构与启动/审核接口相同。优先返回 `waiting_review`；没有待审核草稿时返回最近一份 `completed`。
- **没有可显示任务时**：

```json
{
  "code": 200,
  "message": "当前没有待审核的研究",
  "data": null
}
```

- **说明**：
  - 报告正文来自 LangGraph SQLite 检查点，任务归属来自 MySQL `research_run`。
  - 检查点缺失时，该行会被标为 `abandoned`，接口返回 `data: null`。
  - 前端进入 `/ai` 时调用此接口，用于恢复待审核草稿或已完成报告。

#### 5. 清空当前研究

- **接口地址**：`DELETE /api/ai/research/current`
- **请求头**：需要认证
- **请求参数**：无

- **响应示例**：

```json
{
  "code": 200,
  "message": "研究记录已清空",
  "data": {
    "cleared": 1
  }
}
```

- **说明**：
  - 将当前用户所有 `waiting_review` 和 `completed` 记录改为 `abandoned`（软删除），行仍保留。
  - 前端「清空记录」走此接口；页面上本地「放弃审核」不会调用它，因此刷新后仍可能恢复该草稿。

#### 6. 自动选择模式

- **接口地址**：`POST /api/ai/auto`
- **请求头**：需要认证
- **请求参数**：与普通 AI 对话相同，包含必填的 `message` 和可选的 `history`。

- **请求示例**：

```json
{
  "message": "研究最近一周 AI Agent 的重要新闻",
  "history": []
}
```

Auto 会返回 `chat`、`research` 或 `clarify`，并且三个结果字段中只有对应分支包含内容。

- **Chat 分支响应**：

```json
{
  "code": 200,
  "message": "已使用普通对话模式",
  "data": {
    "selected_mode": "chat",
    "chat_result": {
      "answer": "……"
    },
    "research_result": null,
    "clarification_question": null
  }
}
```

- **Research 分支响应**：

```json
{
  "code": 200,
  "message": "已启动深度研究模式",
  "data": {
    "selected_mode": "research",
    "chat_result": null,
    "research_result": {
      "thread_id": "950ab24d-0b03-4c15-9ac8-bca4b6f833f9",
      "status": "waiting_review",
      "instruction": "请审核新闻研究报告草稿。",
      "draft_report": "# 新闻研究报告\n\n……",
      "final_report": null,
      "search_round": 3,
      "hard_max_search_rounds": 5,
      "allowed_actions": [
        "approve",
        "revise",
        "research_more",
        "change_goal"
      ]
    },
    "clarification_question": null
  }
}
```

- **Clarify 分支响应**：

```json
{
  "code": 200,
  "message": "需要补充信息",
  "data": {
    "selected_mode": "clarify",
    "chat_result": null,
    "research_result": null,
    "clarification_question": "你希望研究哪个公司或产品的近期动态？"
  }
}
```

- **说明**：
  - Auto 的 Chat 分支会使用 `history`；Research 分支当前只把本次 `message` 作为研究目标，不读取 `history`。
  - Research 分支由 Router 调用 `start_research_for_user`，与直接调用 `/api/ai/research/start` 一样会写入 `research_run`。
  - Clarify 只返回澄清问题，不在后端保存待澄清状态。客户端收到用户补充后，应组合成完整问题并重新调用 `/api/ai/auto`。

#### 7. AI 接口运行限制与错误处理

- 前端当前为 Chat 设置 60 秒超时，为 Auto、Research 启动和审核设置 300 秒超时；其他客户端也应为同步研究请求设置单独的长超时。
- Research 使用 LangGraph `SqliteSaver`（`data/research_checkpoints.db`）保存图状态，使用 MySQL `research_run` 保存任务归属。进程重启后，属于当前用户的 `thread_id` 仍可通过 `GET /current` 恢复。
- Chat 消息仍不写入 `ai_chat` 表。研究报告正文在检查点中，任务元数据在 `research_run`。
- 研究证据来自站内标题/简介摘要和 Tavily 新闻摘要，不抓取站外正文，也不读取收藏或浏览历史。
- 字段缺失、类型错误或非法枚举值返回 HTTP 422，格式见文档开头。
- 审核他人任务返回 HTTP 403；对非待审核任务提交审核返回 HTTP 409。
- `revise` 或 `change_goal` 缺少有效反馈、超过硬上限仍提交 `research_more`，当前可能进入 HTTP 500，而不是 400。
- LLM 鉴权、模型调用、结构化输出或搜索工具失败也会进入 HTTP 500。
- 站内搜索异常时本轮退回只搜站外，终端会打印「站内搜索失败，回退到站外」。
