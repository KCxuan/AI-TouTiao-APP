import request from './request'

// ===== 浏览历史模块 =====
// 注意：删除单条记录使用 historyId（浏览记录主键），与新闻 ID 不同

// 添加浏览记录
export function addHistory(newsId) {
  return request.post('/api/history/add', { newsId })
}

// 获取浏览历史列表
export function getHistoryList(page = 1, pageSize = 10) {
  return request.get('/api/history/list', { params: { page, pageSize } })
}

// 删除单条浏览记录
export function deleteHistory(historyId) {
  return request.delete(`/api/history/delete/${historyId}`)
}

// 清空浏览历史
export function clearHistory() {
  return request.delete('/api/history/clear')
}
