import request from './request'

// ===== 收藏模块 =====

// 检查收藏状态
export function checkFavorite(newsId) {
  return request.get('/api/favorite/check', { params: { newsId } })
}

// 添加收藏
export function addFavorite(newsId) {
  return request.post('/api/favorite/add', { newsId })
}

// 取消收藏
export function removeFavorite(newsId) {
  return request.delete('/api/favorite/remove', { params: { newsId } })
}

// 获取收藏列表
export function getFavoriteList(page = 1, pageSize = 10) {
  return request.get('/api/favorite/list', { params: { page, pageSize } })
}

// 清空所有收藏
export function clearFavorites() {
  return request.delete('/api/favorite/clear')
}
