// 兼容新闻列表（ORM snake_case）与详情接口（camelCase）两种字段命名
export function pick(item, ...keys) {
  for (const key of keys) {
    if (item[key] !== undefined && item[key] !== null && item[key] !== '') {
      return item[key]
    }
  }
  return null
}

// 时间格式化：ISO / 带时区字符串 → "2025-08-20 14:30"
export function formatTime(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`
}

// 浏览量显示
export function formatViews(views) {
  const n = Number(views) || 0
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return String(n)
}

// 性别标签映射
export function genderLabel(gender) {
  const map = { male: '男', female: '女', unknown: '保密' }
  return map[gender] || '保密'
}

// 相对时间（用于收藏/历史列表）
export function timeAgo(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return formatTime(value)
  const diff = Date.now() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return formatTime(value)
}
