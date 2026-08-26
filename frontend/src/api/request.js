import axios from 'axios'

// 后端 FastAPI 服务地址（main.py CORS 已放行 5173 端口）
const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000
})

// 请求拦截器：注入认证头
// 后端 utils/auth.py 使用 authorization.split(" ")[1] 取 token，
// 因此格式必须为 "Bearer <token>"
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('toutiao_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 从错误响应中提取可读信息（兼容 {code,message,data} 与 FastAPI 默认 {detail} 两种格式）
function extractErrorMessage(error) {
  const resData = error.response?.data
  if (resData) {
    if (resData.message) return resData.message
    if (Array.isArray(resData.detail)) {
      return resData.detail.map((item) => item.msg).join('；')
    }
    if (resData.detail) return resData.detail
  }
  if (error.code === 'ECONNABORTED') return '请求处理超时，请稍后重试'
  if (!error.response) return '网络异常，无法连接后端服务（localhost:8000）'
  return `请求失败（HTTP ${error.response.status}）`
}

// 响应拦截器：统一处理 {code, message, data} 结构
request.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 200) {
        // 返回整个响应体，调用方自行取 .data / .message
        return body
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  (error) => {
    // 401：token 缺失/过期，清除本地登录态并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('toutiao_token')
      localStorage.removeItem('toutiao_user')
      // 避免循环依赖，这里用 location 跳转而不是 router
      const current = window.location.pathname + window.location.search
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      }
      return Promise.reject(new Error('登录已失效，请重新登录'))
    }
    return Promise.reject(new Error(extractErrorMessage(error)))
  }
)

export default request
