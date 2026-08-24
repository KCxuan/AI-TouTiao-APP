// AI 对话能力：前端直连 AI 开放平台（OpenAI 兼容接口，默认 DeepSeek）
// 与后端无关，API Key 保存在浏览器 localStorage；Base URL / 模型名均可自定义

const CONFIG_KEY = 'toutiao_ai_config'

export const DEFAULT_AI_CONFIG = {
  baseUrl: 'https://api.deepseek.com',
  model: 'deepseek-chat',
  apiKey: ''
}

// 预置模型（DeepSeek 开放平台，也可选"其他模型"手动输入）
export const MODEL_PRESETS = [
  { value: 'deepseek-chat', label: 'deepseek-chat（通用对话）' },
  { value: 'deepseek-reasoner', label: 'deepseek-reasoner（深度思考）' },
  {
    value: 'deepseek-v4-flash-vision-exp',
    label: 'deepseek-v4-flash-vision-exp（多模态，支持图片）'
  },
  { value: 'custom', label: '其他模型（手动输入）' }
]

export function getAIConfig() {
  try {
    const raw = localStorage.getItem(CONFIG_KEY)
    if (raw) {
      return { ...DEFAULT_AI_CONFIG, ...JSON.parse(raw) }
    }
  } catch (e) {
    /* 配置损坏时回退默认值 */
  }
  return { ...DEFAULT_AI_CONFIG }
}

export function saveAIConfig(config) {
  localStorage.setItem(
    CONFIG_KEY,
    JSON.stringify({
      baseUrl: config.baseUrl || DEFAULT_AI_CONFIG.baseUrl,
      model: config.model || DEFAULT_AI_CONFIG.model,
      apiKey: config.apiKey || ''
    })
  )
}

export function hasAIKey() {
  return !!getAIConfig().apiKey
}

/**
 * 流式对话：POST {baseUrl}/chat/completions（stream: true）
 * @param {Object} options
 * @param {Array<{role: string, content: string}>} options.messages 含 system 的完整消息列表
 * @param {(delta: string, full: string) => void} [options.onDelta] 增量回调
 * @param {AbortSignal} [options.signal] 取消信号
 * @returns {Promise<string>} 完整回复文本
 */
export async function streamChatCompletion({ messages, onDelta, signal }) {
  const { baseUrl, apiKey, model } = getAIConfig()
  if (!apiKey) {
    throw new Error('尚未配置 API Key，请点击右上角"设置"填写')
  }

  let res
  try {
    res = await fetch(`${baseUrl.replace(/\/+$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({ model, messages, stream: true }),
      signal
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new Error('无法连接 AI 服务，请检查网络或接口地址是否正确')
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const err = await res.json()
      detail = err.error?.message || err.message || detail
    } catch (e) {
      /* 保持 HTTP 状态码提示 */
    }
    if (res.status === 401) {
      throw new Error(`API Key 无效或未授权：${detail}`)
    }
    throw new Error(`AI 服务返回错误：${detail}`)
  }

  // 解析 SSE 流：每行 "data: {json}"，以 "data: [DONE]" 结束
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let full = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() // 最后一段可能不完整，留到下一轮
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data:')) continue
      const payload = trimmed.slice(5).trim()
      if (payload === '[DONE]') return full
      try {
        const chunk = JSON.parse(payload)
        const delta = chunk.choices?.[0]?.delta?.content || ''
        if (delta) {
          full += delta
          onDelta && onDelta(delta, full)
        }
      } catch (e) {
        /* 忽略无法解析的片段 */
      }
    }
  }
  return full
}
