import request from './request'

const CHAT_TIMEOUT = 60000
const RESEARCH_TIMEOUT = 300000

/**
 * 普通对话。
 * history 只包含本次消息之前已经完成的用户与助手消息。
 */
export async function chatWithAI(message, history = []) {
  const response = await request.post(
    '/api/ai/chat',
    { message, history },
    { timeout: CHAT_TIMEOUT }
  )

  return response.data
}

/**
 * 自动判断本次消息应该进入普通对话、深度研究还是澄清流程。
 */
export async function autoWithAI(message, history = []) {
  const response = await request.post(
    '/api/ai/auto',
    { message, history },
    { timeout: RESEARCH_TIMEOUT }
  )

  return response.data
}

/**
 * 读取当前用户最近若干轮 Chat 问答（时间正序）。
 * 仅包含明确使用对话模式写入的记录。
 */
export async function getChatHistory(limit = 20) {
  const response = await request.get('/api/ai/chat/history', {
    params: { limit }
  })
  return response.data
}

/** 清空当前用户已落库的 Chat 记录。 */
export async function clearChatHistory() {
  const response = await request.delete('/api/ai/chat/history')
  return response.data
}

/**
 * 读取当前登录用户应显示的研究：
 * 优先待审核草稿，否则最近一份已完成报告。
 * 没有可显示任务时返回 null。
 */
export async function getCurrentResearch() {
  const response = await request.get('/api/ai/research/current')
  return response.data
}

/** 清空当前用户可恢复的研究记录（待审核 + 已完成）。 */
export async function clearCurrentResearch() {
  const response = await request.delete('/api/ai/research/current')
  return response.data
}

/**
 * 启动一次新的新闻研究，返回草稿与 LangGraph thread_id。
 */
export async function startResearch(userInput) {
  const response = await request.post(
    '/api/ai/research/start',
    { user_input: userInput },
    { timeout: RESEARCH_TIMEOUT }
  )

  return response.data
}

/**
 * 对研究草稿执行通过、修改、补查或调整目标。
 */
export async function reviewResearch(threadId, action, feedback = null) {
  const response = await request.post(
    `/api/ai/research/${threadId}/review`,
    { action, feedback },
    { timeout: RESEARCH_TIMEOUT }
  )

  return response.data
}
