# API 接口文档

## 概述

本文档详细描述了新闻系统的API接口，包括用户管理、新闻浏览、收藏和历史记录等功能模块。

## 基础URL

```
http://localhost:8000
```

## 认证方式

大部分接口需要认证，认证通过在请求头中添加 `Authorization` 字段实现：

```
Authorization: token值
```

## 响应格式

所有接口返回JSON格式数据，通用响应结构如下：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 接口详情

### 用户管理模块

#### 1. 用户注册

- **接口地址**: `POST /api/user/register`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

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
      "bio": "这个人很懒，什么都没留下",
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    }
  }
}
```

#### 2. 用户登录

- **接口地址**: `POST /api/user/login`
- **请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

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
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
      "bio": "这个人很懒，什么都没留下"
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
  "message": "success",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这个人很懒，什么都没留下"
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
  "message": "更新成功",
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
  "message": "密码修改成功",
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
        "category": null,
        "title": "新闻标题",
        "description": "新闻简介",
        "content": "新闻内容",
        "image": null,
        "author": null,
        "category_id": 1,
        "views": 0
      }
    ],
    "total": 100,
    "hasMore": true
  }
}
```

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
  "message": "success",
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
  "message": "收藏成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "createTime": "2023-01-01T00:00:00"
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
  "message": "取消收藏成功",
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
  "message": "success",
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
  "message": "成功删除1条收藏记录",
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
  "message": "添加成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "viewTime": "2023-01-01T00:00:00"
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
  "message": "success",
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
        "historyId": "",
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
  "message": "删除成功",
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
  "message": "清空成功",
  "data": null
}
```