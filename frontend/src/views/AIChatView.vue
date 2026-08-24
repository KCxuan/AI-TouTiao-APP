<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import {
  streamChatCompletion,
  getAIConfig,
  saveAIConfig,
  hasAIKey,
  MODEL_PRESETS
} from '../api/ai'
import { toast } from '../composables/toast'

// AI 人设：头条新闻的问答助手
const SYSTEM_PROMPT =
  '你是"头条新闻"应用的 AI 助手。用户可能会问你新闻时事、科技动态、常识问题，或请求总结、解释某个话题。请用简体中文回答，语气友好简洁；如果涉及新闻时效性内容，请提醒用户你的知识有截止时间，建议结合应用内的最新新闻阅读。'

const SUGGESTIONS = [
  '帮我梳理一下最近人工智能领域有哪些值得关注的进展',
  '用通俗易懂的语言解释一下什么是 Redis 缓存',
  '推荐几类适合通勤时快速浏览的新闻话题',
  '把"大模型"和"传统机器学习"的区别总结成三句话'
]

const messages = ref([]) // { role: 'assistant' | 'user', content: string, error?: boolean }
const inputText = ref('')
const sending = ref(false)
const abortController = ref(null)

const scrollEl = ref(null)
const inputEl = ref(null)
const fileInputRef = ref(null)

// ===== 图片附件 =====
// DeepSeek 的纯文本模型（deepseek-chat / deepseek-reasoner）不支持图片输入；
// 多模态模型（deepseek-v4-flash-vision-exp 等，名称含 vision）支持图片
const pendingImages = ref([]) // { id, dataUrl }
const MAX_IMAGES = 4
const MAX_IMAGE_SIZE = 4 * 1024 * 1024 // 4MB

// 当前配置的 DeepSeek 模型是否为纯文本模型（附带图片时给出提示）
const imageUnsupported = computed(() => {
  if (pendingImages.value.length === 0) return false
  const model = (getAIConfig().model || '').toLowerCase()
  return model.startsWith('deepseek') && !model.includes('vision')
})

// ===== 设置弹窗 =====
const settingsOpen = ref(false)
const settings = reactive({
  apiKey: '',
  baseUrl: '',
  model: 'deepseek-chat',
  customModel: ''
})

onMounted(() => {
  const cfg = getAIConfig()
  settings.apiKey = cfg.apiKey
  settings.baseUrl = cfg.baseUrl
  settings.model = MODEL_PRESETS.some((m) => m.value === cfg.model)
    ? cfg.model
    : 'custom'
  settings.customModel = settings.model === 'custom' ? cfg.model : ''
  // 首次使用未配置 Key 时自动打开设置
  if (!hasAIKey()) {
    settingsOpen.value = true
  }
})

function openSettings() {
  settingsOpen.value = true
}

function handleSaveSettings() {
  if (!settings.apiKey.trim()) {
    toast('请填写 API Key', 'error')
    return
  }
  const model =
    settings.model === 'custom' ? settings.customModel.trim() : settings.model
  if (!model) {
    toast('请填写模型名称', 'error')
    return
  }
  saveAIConfig({
    apiKey: settings.apiKey.trim(),
    baseUrl: settings.baseUrl.trim(),
    model
  })
  settingsOpen.value = false
  toast('AI 配置已保存', 'success')
}

// ===== 对话逻辑 =====
// 将带图片的用户消息转换为 OpenAI 多模态 content 数组格式
function toApiContent(msg) {
  const parts = []
  if (msg.content) {
    parts.push({ type: 'text', text: msg.content })
  }
  ;(msg.images || []).forEach((url) =>
    parts.push({ type: 'image_url', image_url: { url } })
  )
  return parts
}

function buildApiMessages() {
  // 携带 system 提示 + 最近 20 条历史，避免超出上下文
  const history = messages.value
    .filter((m) => !m.error)
    .slice(-20)
    .map((m) => ({ role: m.role, content: m.content, images: m.images }))

  // 仅在最近一条用户消息中携带图片，避免历史图片在多轮对话中反复重传（体积大、计费高）
  for (let i = history.length - 1; i >= 0; i--) {
    if (history[i].role === 'user') {
      if (history[i].images?.length) {
        history[i] = { ...history[i], content: toApiContent(history[i]) }
      }
      break
    }
  }

  const apiMessages = history.map(({ images, ...m }) => m)
  return [{ role: 'system', content: SYSTEM_PROMPT }, ...apiMessages]
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) {
      scrollEl.value.scrollTop = scrollEl.value.scrollHeight
    }
  })
}

async function send(text) {
  const content = (text || inputText.value).trim()
  const images = pendingImages.value.map((img) => img.dataUrl)
  if ((!content && images.length === 0) || sending.value) return
  if (!hasAIKey()) {
    settingsOpen.value = true
    toast('请先配置 AI API Key', 'error')
    return
  }

  messages.value.push({
    role: 'user',
    content,
    images: images.length > 0 ? images : undefined
  })
  pendingImages.value = []
  inputText.value = ''
  autoResize()
  scrollToBottom()

  const reply = reactive({ role: 'assistant', content: '' })
  messages.value.push(reply)

  sending.value = true
  abortController.value = new AbortController()
  try {
    await streamChatCompletion({
      messages: buildApiMessages(),
      signal: abortController.value.signal,
      onDelta: (_delta, full) => {
        reply.content = full
        scrollToBottom()
      }
    })
    if (!reply.content) {
      reply.content = '（AI 未返回内容，请重试或更换模型）'
      reply.error = true
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      // 用户主动停止，保留已生成的部分
      if (!reply.content) {
        messages.value.splice(messages.value.indexOf(reply), 1)
      }
      toast('已停止生成')
    } else {
      reply.content = `出错了：${e.message}`
      reply.error = true
    }
  } finally {
    sending.value = false
    abortController.value = null
    scrollToBottom()
  }
}

function stopGenerating() {
  abortController.value?.abort()
}

function clearChat() {
  if (sending.value) stopGenerating()
  if (messages.value.length === 0) return
  if (window.confirm('确定要清空当前对话吗？')) {
    messages.value = []
    toast('对话已清空')
  }
}

// 等待首个字符时显示打字动画
const waitingFirstToken = computed(
  () => sending.value && messages.value[messages.value.length - 1]?.content === ''
)

// ===== 输入框 =====
function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function autoResize() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 140) + 'px'
}

// ===== 图片附件处理 =====
function addImageFile(file) {
  if (!file.type.startsWith('image/')) {
    toast('仅支持图片文件', 'error')
    return
  }
  if (file.size > MAX_IMAGE_SIZE) {
    toast('图片不能超过 4MB', 'error')
    return
  }
  if (pendingImages.value.length >= MAX_IMAGES) {
    toast(`最多附带 ${MAX_IMAGES} 张图片`, 'error')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    pendingImages.value.push({
      id: Date.now() + Math.random(),
      dataUrl: reader.result
    })
  }
  reader.readAsDataURL(file)
}

// 在输入框粘贴图片（截图后 Ctrl+V）
function handlePaste(e) {
  if (sending.value) return
  const files = Array.from(e.clipboardData?.files || []).filter((f) =>
    f.type.startsWith('image/')
  )
  if (files.length > 0) {
    e.preventDefault()
    files.forEach(addImageFile)
  }
}

function triggerFilePick() {
  fileInputRef.value?.click()
}

function onFileChange(e) {
  Array.from(e.target.files || []).forEach(addImageFile)
  e.target.value = '' // 允许重复选择同一张图
}

function removeImage(id) {
  pendingImages.value = pendingImages.value.filter((img) => img.id !== id)
}

// ===== 轻量 Markdown 渲染（先转义再替换，保证安全） =====
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderContent(content) {
  let html = escapeHtml(content || '')
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\n/g, '<br>')
  return html
}
</script>

<template>
  <div class="container chat-page">
    <div class="card chat-card">
      <!-- 顶栏 -->
      <div class="chat-head">
        <div class="chat-head-left">
          <span class="ai-badge">AI</span>
          <div>
            <h1 class="chat-title">AI 问答</h1>
            <p class="chat-sub">问我新闻、科技、或者任何事</p>
          </div>
        </div>
        <div class="chat-head-actions">
          <button class="btn btn-text" @click="openSettings">⚙ 设置</button>
          <button class="btn btn-text" @click="clearChat">清空对话</button>
        </div>
      </div>

      <!-- 消息区 -->
      <div class="chat-body" ref="scrollEl">
        <!-- 欢迎态 -->
        <div v-if="messages.length === 0" class="chat-welcome">
          <div class="welcome-icon">✦</div>
          <h2 class="welcome-title">你好，我是头条 AI 助手</h2>
          <p class="welcome-sub">
            可以问我新闻时事、科技动态，也可以让我解释概念、总结内容
          </p>
          <div class="suggestion-list">
            <button
              v-for="s in SUGGESTIONS"
              :key="s"
              class="suggestion-chip"
              :disabled="sending"
              @click="send(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- 对话气泡 -->
        <template v-else>
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="msg-row"
            :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'"
          >
            <div v-if="msg.role === 'assistant'" class="msg-avatar">AI</div>

            <div
              v-if="msg.role === 'assistant'"
              class="msg-bubble"
              :class="{ 'msg-error': msg.error }"
            >
              <span
                v-if="waitingFirstToken && idx === messages.length - 1"
                class="typing-dots"
              >
                <i></i><i></i><i></i>
              </span>
              <!-- eslint-disable-next-line vue/no-v-html -->
              <span v-else v-html="renderContent(msg.content)"></span>
            </div>

            <!-- 用户消息：图片预览 + 文本气泡 -->
            <div v-else class="msg-user-stack">
              <div v-if="msg.images?.length" class="msg-images">
                <img
                  v-for="(img, i) in msg.images"
                  :key="i"
                  :src="img"
                  alt="附件图片"
                  class="msg-image"
                />
              </div>
              <div v-if="msg.content" class="msg-bubble">{{ msg.content }}</div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <!-- 待发送图片预览 -->
        <div v-if="pendingImages.length" class="pending-images">
          <div v-for="img in pendingImages" :key="img.id" class="pending-thumb">
            <img :src="img.dataUrl" alt="待发送图片" />
            <button class="thumb-remove" title="移除" @click="removeImage(img.id)">
              ✕
            </button>
          </div>
        </div>

        <div class="chat-input-row">
          <button
            class="btn btn-text attach-btn"
            :disabled="sending"
            title="添加图片"
            @click="triggerFilePick"
          >
            📎
          </button>
          <textarea
            ref="inputEl"
            v-model="inputText"
            class="chat-input"
            rows="1"
            placeholder="输入你的问题…（Enter 发送，Shift + Enter 换行，可 Ctrl+V 粘贴图片）"
            :disabled="sending"
            @keydown="handleKeydown"
            @input="autoResize"
            @paste="handlePaste"
          ></textarea>
          <button
            v-if="sending"
            class="btn btn-outline send-btn"
            @click="stopGenerating"
          >
            停止
          </button>
          <button
            v-else
            class="btn btn-primary send-btn"
            :disabled="!inputText.trim() && pendingImages.length === 0"
            @click="send()"
          >
            发送
          </button>
        </div>

        <p v-if="imageUnsupported" class="image-warn">
          ⚠ 当前模型（{{ (getAIConfig().model || '').toLowerCase() }}）为纯文本模型，不支持图片输入，发送后会报错；可在「设置」中切换为 deepseek-v4-flash-vision-exp
        </p>

        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          multiple
          hidden
          @change="onFileChange"
        />
      </div>
    </div>

    <!-- 设置弹窗 -->
    <Teleport to="body">
      <div
        v-if="settingsOpen"
        class="modal-overlay"
        @click.self="settingsOpen = false"
      >
        <div class="card modal-card">
          <h2 class="modal-title">AI 服务配置</h2>
          <p class="modal-hint">
            默认对接 DeepSeek 开放平台（platform.deepseek.com），接口为
            OpenAI 兼容格式；Base URL、模型名均可自定义以接入其他兼容服务，Key
            仅保存在本地浏览器中。
          </p>

          <div class="field">
            <label for="aiKey">API Key</label>
            <input
              id="aiKey"
              v-model="settings.apiKey"
              type="password"
              placeholder="在 DeepSeek 开放平台「API Keys」页面创建并复制"
              autocomplete="off"
            />
          </div>

          <div class="field">
            <label for="aiBaseUrl">接口地址（Base URL）</label>
            <input id="aiBaseUrl" v-model="settings.baseUrl" type="text" />
          </div>

          <div class="field">
            <label for="aiModel">模型</label>
            <select id="aiModel" v-model="settings.model">
              <option
                v-for="m in MODEL_PRESETS"
                :key="m.value"
                :value="m.value"
              >
                {{ m.label }}
              </option>
            </select>
          </div>

          <div v-if="settings.model === 'custom'" class="field">
            <label for="aiCustomModel">模型名称</label>
            <input
              id="aiCustomModel"
              v-model="settings.customModel"
              type="text"
              placeholder="例如：deepseek-coder / 其他 OpenAI 兼容模型"
            />
          </div>

          <div class="modal-actions">
            <button class="btn btn-outline" @click="settingsOpen = false">
              取消
            </button>
            <button class="btn btn-primary" @click="handleSaveSettings">
              保存
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
}

.chat-card {
  flex: 1;
  height: calc(100vh - 160px);
  min-height: 480px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶栏 */
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.chat-head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-badge {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  border-radius: var(--radius-md);
}

.chat-title {
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 600;
  line-height: 1.3;
}

.chat-sub {
  font-size: 12.5px;
  color: var(--text-tertiary);
}

.chat-head-actions {
  display: flex;
  gap: 4px;
}

/* 消息区 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 欢迎态 */
.chat-welcome {
  margin: auto;
  text-align: center;
  max-width: 520px;
  padding: 24px 0;
}

.welcome-icon {
  font-size: 40px;
  color: var(--accent);
  margin-bottom: 12px;
}

.welcome-title {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.welcome-sub {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 24px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-chip {
  text-align: left;
  padding: 12px 18px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background-color: var(--surface);
  font-size: 14px;
  color: var(--text-primary);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.suggestion-chip:hover:not(:disabled) {
  border-color: var(--accent);
  background-color: var(--accent-soft);
}

.suggestion-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 气泡 */
.msg-row {
  display: flex;
  gap: 12px;
  max-width: 86%;
}

.msg-row.msg-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

/* 用户消息：图片 + 文本纵向堆叠，右对齐 */
.msg-user-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  max-width: 100%;
}

.msg-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.msg-image {
  max-width: 220px;
  max-height: 160px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-strong);
  object-fit: cover;
  display: block;
}

.msg-row.msg-ai {
  align-self: flex-start;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 700;
  border-radius: 50%;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14.5px;
  line-height: 1.75;
  word-break: break-word;
}

.msg-ai .msg-bubble {
  background-color: var(--surface);
  border: 1px solid var(--border);
}

.msg-user .msg-bubble {
  background-color: var(--accent);
  color: #fff;
}

.msg-bubble.msg-error {
  color: var(--error);
  background-color: var(--error-soft);
  border-color: var(--error);
}

.msg-bubble :deep(code) {
  background-color: rgba(31, 30, 29, 0.06);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: Consolas, Menlo, monospace;
  font-size: 13px;
}

.msg-user .msg-bubble :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
}

/* 打字动画 */
.typing-dots {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  padding: 4px 0;
}

.typing-dots i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--text-tertiary);
  animation: typing 1.2s infinite ease-in-out;
}

.typing-dots i:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* 输入区 */
.chat-input-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  background-color: var(--surface);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.chat-input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.attach-btn {
  font-size: 18px;
  padding: 8px 10px;
  flex-shrink: 0;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  line-height: 1;
}

.attach-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 待发送图片缩略图 */
.pending-images {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pending-thumb {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-strong);
  background-color: var(--bg);
}

.pending-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: rgba(31, 30, 29, 0.65);
  color: #fff;
  font-size: 11px;
  line-height: 1;
}

.thumb-remove:hover {
  background-color: var(--error);
}

.image-warn {
  font-size: 12.5px;
  color: var(--error);
  background-color: var(--error-soft);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
}

.chat-input {
  flex: 1;
  resize: none;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  line-height: 1.6;
  font-size: 14.5px;
  outline: none;
  background-color: var(--surface-white);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.chat-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.chat-input:disabled {
  opacity: 0.6;
}

.send-btn {
  flex-shrink: 0;
  min-width: 84px;
}

/* 设置弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  background-color: rgba(31, 30, 29, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 100%;
  max-width: 440px;
  padding: 28px 30px;
}

.modal-title {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.modal-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .msg-row {
    max-width: 100%;
  }

  .chat-sub {
    display: none;
  }
}
</style>
