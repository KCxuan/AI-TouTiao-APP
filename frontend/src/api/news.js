import request from './request'

// ===== 新闻模块 =====

// 获取新闻分类列表
export function getCategories(skip = 0, limit = 100) {
  return request.get('/api/news/categories', { params: { skip, limit } })
}

// 获取新闻列表（分页），返回 { list, total, hasMore }
export function getNewsList(categoryId, page = 1, pageSize = 10) {
  return request.get('/api/news/list', {
    params: { categoryId, page, pageSize }
  })
}

// 关键词搜索（分页），返回 { list, total, hasMore, keyword, categoryId }
// categoryId 不传或传 null 时全站搜索
export function searchNews(keyword, page = 1, pageSize = 10, categoryId = null) {
  const params = { q: keyword, page, pageSize }
  if (categoryId != null) {
    params.categoryId = categoryId
  }
  return request.get('/api/news/search', { params })
}

// 获取新闻详情，返回含 relatedNews
export function getNewsDetail(id) {
  return request.get('/api/news/detail', { params: { id } })
}

// 发布新闻（需登录），author 由服务端填充为当前用户名
export function publishNews(data) {
  return request.post('/api/news/publish', {
    title: data.title,
    description: data.description || null,
    content: data.content,
    image: data.image || null,
    categoryId: data.categoryId
  })
}

// 获取当前登录用户自己发布的新闻列表（不缓存，个人数据直查）
export function getMyNewsList(page = 1, pageSize = 10) {
  return request.get('/api/news/mine', { params: { page, pageSize } })
}

// 编辑自己发布的新闻（部分更新：只改传入的字段）
export function updateNews(data) {
  return request.put('/api/news/update', {
    id: data.id,
    title: data.title,
    description: data.description || null,
    content: data.content,
    image: data.image || null,
    categoryId: data.categoryId
  })
}

// 删除自己发布的新闻
export function deleteNews(newsId) {
  return request.delete(`/api/news/delete/${newsId}`)
}
