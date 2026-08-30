<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import {
  autoWithAI,
  chatWithAI,
  clearChatHistory,
  clearCurrentResearch,
  getChatHistory,
  getCurrentResearch,
  reviewResearch,
  startResearch
} from '../api/ai'
import { toast } from '../composables/toast'

const MODES = [
  {
    id: 'auto',
    shortLabel: '自动',
    title: '自动判断',
    description: '由助手判断是直接回答、发起研究，还是先向你确认问题。',
    action: '交给助手'
  },
  {
    id: 'chat',
    shortLabel: '对话',
    title: '普通对话',
    description: '适合解释概念、讨论想法，以及处理不需要实时检索的问题。',
    action: '发送问题'
  },
  {
    id: 'research',
    shortLabel: '研究',
    title: '深度研究',
    description: '搜索外部新闻、检查证据，并生成一份等待你审核的报告。',
    action: '开始研究'
  }
]

const SUGGESTIONS = {
  auto: [
    '研究最近一周 AI Agent 领域的重要新闻，并标出信息来源',
    '用通俗的语言解释 LangGraph 中 State 的作用',
    '帮我核查近期“AI 手机”相关报道中的主要说法',
    '比较工作流和 Agent 的区别，并举一个新闻项目的例子'
  ],
  chat: [
    '用一个生活中的例子解释什么是 Service 层',
    'LangGraph 的 State 为什么通常使用 TypedDict？',
    '帮我总结普通对话模式与深度研究模式的区别',
    '解释 FastAPI Router 到 Service 的调用过程'
  ],
  research: [
    '研究最近一周 AI Agent 领域的重要新闻，并整理时间线',
    '对比近期几家主要 AI 公司的产品进展，并引用来源',
    '核查最近有关 AI 手机的主要说法与不同媒体观点',
    '研究一个近期科技事件的起因、进展与可能影响'
  ]
}

const REVIEW_ACTIONS = {
  approve: {
    label: '通过并定稿',
    done: '报告已经通过审核并生成最终版本。'
  },
  revise: {
    label: '修改草稿',
    prompt: '请写下希望怎样修改这份报告',
    placeholder: '例如：缩短背景部分，加强不同厂商之间的比较……',
    required: true,
    done: '报告已按照修改意见重新生成。'
  },
  research_more: {
    label: '补充检索',
    prompt: '还希望重点补查什么？',
    placeholder: '可选，例如：补充英文来源或查找更近期的报道……',
    required: false,
    done: '已补充检索并生成新的报告草稿。'
  },
  change_goal: {
    label: '调整目标',
    prompt: '请输入新的完整研究目标',
    placeholder: '例如：研究最近一个月 AI 手机在端侧模型方面的进展……',
    required: true,
    done: '已按新的研究目标重新开始并生成草稿。'
  }
}

const selectedMode = ref('auto')
const phase = ref('idle')
const messages = ref([])
const inputText = ref('')
const pendingClarification = ref(null)
const activeResearchMessageId = ref(null)
const restoring = ref(true)

const scrollEl = ref(null)
const inputEl = ref(null)

let messageSequence = 0

const activeMode = computed(
  () => MODES.find((mode) => mode.id === selectedMode.value) || MODES[0]
)

const suggestions = computed(() => SUGGESTIONS[selectedMode.value])

const interfaceLocked = computed(
  () => restoring.value || phase.value !== 'idle'
)

const inputPlaceholder = computed(() => {
  if (restoring.value) {
    return '正在恢复上次的对话'
  }
  if (phase.value === 'waiting_review') {
    return '请先审核上方的研究报告草稿'
  }
  if (phase.value === 'reviewing') {
    return '正在根据你的审核决定继续处理'
  }
  if (phase.value === 'requesting') {
    return '正在处理当前请求'
  }
  if (pendingClarification.value) {
    return '补充研究对象、时间范围或你最关心的方面'
  }
  return '写下你想讨论或研究的问题……'
})

const busyText = computed(() => {
  if (phase.value === 'reviewing') return '正在处理审核决定'
  if (selectedMode.value === 'research') return '正在检索并核对新闻证据'
  if (selectedMode.value === 'auto') return '正在判断并处理你的请求'
  return '正在组织回答'
})

function nextMessageId() {
  messageSequence += 1
  return `message-${Date.now()}-${messageSequence}`
}

function chooseMode(mode) {
  if (interfaceLocked.value) return
  selectedMode.value = mode
  pendingClarification.value = null
}

function buildHistory() {
  return messages.value
    .filter((message) => message.historyEligible)
    .slice(-20)
    .map((message) => ({
      role: message.role,
      content: message.historyContent || message.content
    }))
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) {
      scrollEl.value.scrollTop = scrollEl.value.scrollHeight
    }
  })
}

function autoResize() {
  const element = inputEl.value
  if (!element) return
  element.style.height = 'auto'
  element.style.height = Math.min(element.scrollHeight, 160) + 'px'
}

function handleKeydown(event) {
  if (event.isComposing) return
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

function setTextReply(reply, userMessage, content, resolvedMode, label) {
  reply.kind = resolvedMode === 'clarify' ? 'clarification' : 'text'
  reply.content = content
  reply.resolvedMode = resolvedMode
  reply.label = label

  if (resolvedMode === 'chat') {
    userMessage.historyEligible = true
    reply.historyEligible = true
  }
}

function setResearchReply(reply, research, label) {
  reply.kind = 'research'
  reply.label = label
  reply.resolvedMode = 'research'
  reply.research = research
  reply.content = research.final_report || research.draft_report || ''
  reply.pendingAction = null
  reply.feedback = ''
  reply.revisionCount = 0

  if (research.status === 'waiting_review') {
    activeResearchMessageId.value = reply.id
    phase.value = 'waiting_review'
  } else {
    phase.value = 'idle'
  }
}

function restoreResearch(research) {
  selectedMode.value = 'research'

  const userMessage = {
    id: nextMessageId(),
    role: 'user',
    kind: 'text',
    content: research.user_input || '（已恢复的研究主题）',
    historyEligible: false,
    requestedMode: 'research',
    modeLabel: '研究'
  }

  const reply = {
    id: nextMessageId(),
    role: 'assistant',
    kind: 'loading',
    content: '',
    historyEligible: false,
    requestedMode: 'research',
    resolvedMode: null,
    label: '深度研究'
  }

  messages.value.push(userMessage, reply)
  const restoredLabel =
    research.status === 'completed' ? '深度研究 · 已完成' : '深度研究 · 已恢复'
  setResearchReply(reply, research, restoredLabel)
  scrollToBottom()
}

function restoreChatTurns(turns) {
  const restored = []
  for (const turn of turns || []) {
    restored.push({
      id: `chat-${turn.id}-user`,
      role: 'user',
      kind: 'text',
      content: turn.message,
      historyEligible: true,
      requestedMode: 'chat',
      modeLabel: '对话'
    })
    restored.push({
      id: `chat-${turn.id}-assistant`,
      role: 'assistant',
      kind: 'text',
      content: turn.response,
      historyEligible: true,
      requestedMode: 'chat',
      resolvedMode: 'chat',
      label: '普通对话'
    })
  }
  return restored
}

onMounted(async () => {
  try {
    const [historyResult, research] = await Promise.all([
      getChatHistory(),
      getCurrentResearch()
    ])

    messages.value = restoreChatTurns(historyResult?.list)

    const restoredChat = (historyResult?.list || []).length > 0
    const hasResearch =
      research &&
      (research.status === 'waiting_review' || research.status === 'completed')

    if (hasResearch) {
      restoreResearch(research)
      if (research.status === 'waiting_review') {
        toast(
          restoredChat
            ? '已恢复最近对话和未完成的研究报告'
            : '已恢复未完成的研究报告'
        )
      } else {
        toast(
          restoredChat
            ? '已恢复最近对话和完成的研究报告'
            : '已恢复完成的研究报告'
        )
      }
    } else if (restoredChat) {
      toast('已恢复最近对话')
      scrollToBottom()
    }
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    restoring.value = false
  }
})

async function send(text) {
  const content = (text || inputText.value).trim()
  if (!content || interfaceLocked.value) return

  const history = buildHistory()
  const clarification = pendingClarification.value
  const effectiveMessage =
    selectedMode.value === 'auto' && clarification
      ? `原始请求：${clarification.originalMessage}\n用户补充：${content}`
      : content

  const userMessage = {
    id: nextMessageId(),
    role: 'user',
    kind: 'text',
    content,
    historyContent: effectiveMessage,
    historyEligible: false,
    requestedMode: selectedMode.value,
    modeLabel: activeMode.value.shortLabel
  }

  const reply = {
    id: nextMessageId(),
    role: 'assistant',
    kind: 'loading',
    content: '',
    historyEligible: false,
    requestedMode: selectedMode.value,
    resolvedMode: null,
    label: activeMode.value.title
  }

  messages.value.push(userMessage, reply)
  inputText.value = ''
  autoResize()
  phase.value = 'requesting'
  scrollToBottom()

  try {
    if (selectedMode.value === 'chat') {
      const result = await chatWithAI(effectiveMessage, history)
      setTextReply(reply, userMessage, result.answer, 'chat', '普通对话')
      pendingClarification.value = null
      phase.value = 'idle'
      return
    }

    if (selectedMode.value === 'research') {
      const result = await startResearch(effectiveMessage)
      setResearchReply(reply, result, '深度研究')
      pendingClarification.value = null
      return
    }

    const result = await autoWithAI(effectiveMessage, history)

    if (result.selected_mode === 'chat') {
      setTextReply(
        reply,
        userMessage,
        result.chat_result.answer,
        'chat',
        '自动判断 · 普通对话'
      )
      pendingClarification.value = null
      phase.value = 'idle'
      return
    }

    if (result.selected_mode === 'research') {
      setResearchReply(
        reply,
        result.research_result,
        '自动判断 · 深度研究'
      )
      pendingClarification.value = null
      return
    }

    const question =
      result.clarification_question || '请再补充一些研究对象或范围。'
    setTextReply(
      reply,
      userMessage,
      question,
      'clarify',
      '自动判断 · 需要补充'
    )
    pendingClarification.value = {
      originalMessage: effectiveMessage,
      question
    }
    phase.value = 'idle'
  } catch (error) {
    reply.kind = 'error'
    reply.label = '请求未完成'
    reply.content = error.message
    phase.value = 'idle'
    toast(error.message, 'error')
  } finally {
    scrollToBottom()
  }
}

function cancelClarification() {
  pendingClarification.value = null
  inputText.value = ''
}

function openReviewForm(message, action) {
  message.pendingAction = action
  message.feedback = ''
  nextTick(() => {
    document.getElementById(`review-${message.id}`)?.focus()
  })
}

function closeReviewForm(message) {
  message.pendingAction = null
  message.feedback = ''
}

function abandonResearch(message) {
  if (!window.confirm('确定放弃这次研究吗？当前草稿仍会保留在页面中。')) {
    return
  }

  message.abandoned = true
  message.pendingAction = null
  message.feedback = ''
  activeResearchMessageId.value = null
  phase.value = 'idle'
  toast('已关闭本页审核。未完成的研究刷新后仍会恢复；新开研究才会放弃旧草稿。')
}

function actionAllowed(message, action) {
  return message.research.allowed_actions?.includes(action)
}

async function submitReview(message, action = message.pendingAction) {
  if (
    phase.value !== 'waiting_review' ||
    activeResearchMessageId.value !== message.id
  ) {
    return
  }

  const actionInfo = REVIEW_ACTIONS[action]
  const feedback = (message.feedback || '').trim()

  if (actionInfo.required && !feedback) {
    toast('请先填写审核意见', 'error')
    return
  }

  phase.value = 'reviewing'
  message.reviewing = true

  try {
    const result = await reviewResearch(
      message.research.thread_id,
      action,
      feedback || null
    )

    message.research = result
    message.content = result.final_report || result.draft_report || ''
    message.pendingAction = null
    message.feedback = ''
    message.lastReviewMessage = actionInfo.done
    message.revisionCount += 1

    if (result.status === 'completed') {
      activeResearchMessageId.value = null
      phase.value = 'idle'
      toast('研究报告已通过审核', 'success')
    } else {
      phase.value = 'waiting_review'
      toast(actionInfo.done, 'success')
    }
  } catch (error) {
    phase.value = 'waiting_review'
    toast(error.message, 'error')
  } finally {
    message.reviewing = false
    scrollToBottom()
  }
}

async function clearConversation() {
  if (restoring.value || phase.value === 'requesting' || phase.value === 'reviewing') {
    toast('请等待当前请求完成后再清空', 'error')
    return
  }
  if (messages.value.length === 0) return
  if (
    !window.confirm(
      '确定清空当前记录吗？已保存的对话、未完成和已完成的研究都不会再恢复。'
    )
  ) {
    return
  }

  try {
    await Promise.all([clearCurrentResearch(), clearChatHistory()])
    messages.value = []
    pendingClarification.value = null
    activeResearchMessageId.value = null
    phase.value = 'idle'
    toast('记录已清空')
  } catch (error) {
    toast(error.message, 'error')
  }
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderInline(value) {
  let html = escapeHtml(value)
  const links = []

  html = html.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (_match, label, url) => {
      const index = links.length
      links.push(
        `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`
      )
      return `%%NEWS_LINK_${index}%%`
    }
  )
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\[(S\d+)\]/g, '<span class="source-mark">[$1]</span>')
  return html.replace(
    /%%NEWS_LINK_(\d+)%%/g,
    (_match, index) => links[Number(index)]
  )
}

function renderMessage(value) {
  return renderInline(value).replace(/\n/g, '<br>')
}

function parseReport(markdown) {
  const blocks = []
  let currentList = null

  function flushList() {
    if (currentList) {
      blocks.push(currentList)
      currentList = null
    }
  }

  for (const rawLine of String(markdown || '').split('\n')) {
    const line = rawLine.trim()

    if (!line) {
      flushList()
      continue
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/)
    if (heading) {
      flushList()
      blocks.push({
        type: 'heading',
        level: heading[1].length,
        content: heading[2]
      })
      continue
    }

    const bullet = line.match(/^[-*]\s+(.+)$/)
    if (bullet) {
      if (!currentList || currentList.ordered) {
        flushList()
        currentList = { type: 'list', ordered: false, items: [] }
      }
      currentList.items.push(bullet[1])
      continue
    }

    const numbered = line.match(/^\d+[.)]\s+(.+)$/)
    if (numbered) {
      if (!currentList || !currentList.ordered) {
        flushList()
        currentList = { type: 'list', ordered: true, items: [] }
      }
      currentList.items.push(numbered[1])
      continue
    }

    flushList()

    if (line.startsWith('> ')) {
      blocks.push({ type: 'quote', content: line.slice(2) })
    } else {
      blocks.push({ type: 'paragraph', content: line })
    }
  }

  flushList()
  return blocks
}
</script>

<template>
  <div class="container ai-page">
    <section class="ai-shell">
      <aside class="mode-rail">
        <div class="rail-brand">
          <span class="rail-mark" aria-hidden="true">N</span>
          <span>NEWS PILOT</span>
        </div>

        <div class="rail-intro">
          <p class="rail-eyebrow">编辑部研究桌</p>
          <h1>从一个问题，走到有出处的答案。</h1>
          <p>
            快速交流、自动判断，或发起一轮可由你审核的新闻研究。
          </p>
        </div>

        <div class="mode-list" role="group" aria-label="选择 AI 工作模式">
          <button
            v-for="mode in MODES"
            :key="mode.id"
            type="button"
            class="mode-option"
            :class="{ active: selectedMode === mode.id }"
            :aria-pressed="selectedMode === mode.id"
            :disabled="interfaceLocked"
            @click="chooseMode(mode.id)"
          >
            <span class="mode-index">0{{ MODES.indexOf(mode) + 1 }}</span>
            <span class="mode-copy">
              <strong>{{ mode.title }}</strong>
              <small>{{ mode.description }}</small>
            </span>
          </button>
        </div>

        <div class="rail-footer">
          <div class="service-line">
            <span class="service-dot" aria-hidden="true"></span>
            <span>由后端 AI 服务提供能力</span>
          </div>
          <p>模型配置与密钥不再保存在浏览器中。</p>
        </div>
      </aside>

      <section class="conversation-panel">
        <header class="workspace-head">
          <div>
            <p class="workspace-kicker">当前工作方式</p>
            <h2>{{ activeMode.title }}</h2>
          </div>
          <button
            type="button"
            class="clear-button"
            :disabled="
              messages.length === 0 ||
              restoring ||
              phase === 'requesting' ||
              phase === 'reviewing'
            "
            @click="clearConversation"
          >
            清空记录
          </button>
        </header>

        <div
          ref="scrollEl"
          class="conversation-body"
          role="log"
          aria-live="polite"
          :aria-busy="phase === 'requesting' || phase === 'reviewing'"
        >
          <div v-if="restoring" class="welcome">
            <p class="welcome-number">00 / RESTORE</p>
            <h2>正在恢复上次的对话…</h2>
            <p class="welcome-description">
              最近的普通对话，以及未完成或已完成的研究报告，都会重新放到这里。
            </p>
          </div>

          <div v-else-if="messages.length === 0" class="welcome">
            <p class="welcome-number">01 / ASK</p>
            <h2>今天想弄清哪件事？</h2>
            <p class="welcome-description">{{ activeMode.description }}</p>

            <div class="suggestion-grid">
              <button
                v-for="(suggestion, index) in suggestions"
                :key="suggestion"
                type="button"
                class="suggestion"
                @click="send(suggestion)"
              >
                <span>0{{ index + 1 }}</span>
                <strong>{{ suggestion }}</strong>
                <i aria-hidden="true">↗</i>
              </button>
            </div>
          </div>

          <template v-else>
            <article
              v-for="message in messages"
              :key="message.id"
              class="message"
              :class="[
                `message-${message.role}`,
                { 'message-research': message.kind === 'research' }
              ]"
            >
              <template v-if="message.role === 'user'">
                <div class="user-meta">
                  <span>{{ message.modeLabel }}模式</span>
                  <span>你</span>
                </div>
                <div class="user-copy">{{ message.content }}</div>
              </template>

              <template v-else>
                <div class="assistant-meta">
                  <span class="assistant-mark" aria-hidden="true">N</span>
                  <span>{{ message.label }}</span>
                </div>

                <div v-if="message.kind === 'loading'" class="loading-state">
                  <span class="loading-ring" aria-hidden="true"></span>
                  <div>
                    <strong>{{ busyText }}</strong>
                    <p>深度研究可能需要几分钟，请保持当前页面开启。</p>
                  </div>
                </div>

                <div
                  v-else-if="message.kind === 'error'"
                  class="error-state"
                >
                  <strong>这次请求没有完成</strong>
                  <p>{{ message.content }}</p>
                </div>

                <div
                  v-else-if="message.kind === 'clarification'"
                  class="clarification-card"
                >
                  <p class="clarification-label">需要你补充一点信息</p>
                  <div v-html="renderMessage(message.content)"></div>
                </div>

                <section
                  v-else-if="message.kind === 'research'"
                  class="research-card"
                  :class="{
                    completed: message.research.status === 'completed',
                    abandoned: message.abandoned
                  }"
                >
                  <header class="research-head">
                    <div>
                      <p>
                        {{
                          message.abandoned
                            ? 'RESEARCH CLOSED'
                            : message.research.status === 'completed'
                            ? 'FINAL REPORT'
                            : 'RESEARCH DRAFT'
                        }}
                      </p>
                      <h3>
                        {{
                          message.abandoned
                            ? '已保留的研究草稿'
                            : message.research.status === 'completed'
                            ? '新闻研究报告'
                            : '报告草稿，等待你的判断'
                        }}
                      </h3>
                    </div>
                    <span
                      class="status-tag"
                      :class="{
                        final: message.research.status === 'completed',
                        closed: message.abandoned
                      }"
                    >
                      {{
                        message.abandoned
                          ? '已放弃'
                          : message.research.status === 'completed'
                          ? '已完成'
                          : '待审核'
                      }}
                    </span>
                  </header>

                  <div
                    v-if="
                      message.research.status === 'waiting_review' &&
                      !message.abandoned
                    "
                    class="research-facts"
                  >
                    <span>
                      已完成 {{ message.research.search_round }} 轮搜索
                    </span>
                    <span>
                      最多 {{ message.research.hard_max_search_rounds }} 轮
                    </span>
                    <span>{{ message.research.instruction }}</span>
                  </div>

                  <p
                    v-if="message.lastReviewMessage"
                    class="revision-note"
                  >
                    {{ message.lastReviewMessage }}
                  </p>

                  <article class="report-paper">
                    <template
                      v-for="(block, blockIndex) in parseReport(message.content)"
                      :key="`${message.id}-block-${blockIndex}`"
                    >
                      <h2
                        v-if="block.type === 'heading'"
                        class="report-heading"
                        :class="`report-heading-${block.level}`"
                        v-html="renderInline(block.content)"
                      ></h2>

                      <component
                        :is="block.ordered ? 'ol' : 'ul'"
                        v-else-if="block.type === 'list'"
                        class="report-list"
                      >
                        <li
                          v-for="(item, itemIndex) in block.items"
                          :key="itemIndex"
                          v-html="renderInline(item)"
                        ></li>
                      </component>

                      <blockquote
                        v-else-if="block.type === 'quote'"
                        v-html="renderInline(block.content)"
                      ></blockquote>

                      <p
                        v-else
                        v-html="renderInline(block.content)"
                      ></p>
                    </template>
                  </article>

                  <section
                    v-if="
                      message.research.status === 'waiting_review' &&
                      !message.abandoned
                    "
                    class="review-panel"
                  >
                    <div class="review-title">
                      <div>
                        <p>HUMAN REVIEW</p>
                        <h4>这份草稿下一步怎么走？</h4>
                      </div>
                      <span v-if="message.reviewing">正在处理……</span>
                    </div>

                    <div class="review-actions">
                      <button
                        v-if="actionAllowed(message, 'approve')"
                        type="button"
                        class="review-button review-primary"
                        :disabled="message.reviewing"
                        @click="submitReview(message, 'approve')"
                      >
                        通过并定稿
                      </button>
                      <button
                        v-if="actionAllowed(message, 'revise')"
                        type="button"
                        class="review-button"
                        :disabled="message.reviewing"
                        @click="openReviewForm(message, 'revise')"
                      >
                        修改草稿
                      </button>
                      <button
                        v-if="actionAllowed(message, 'research_more')"
                        type="button"
                        class="review-button"
                        :disabled="message.reviewing"
                        @click="openReviewForm(message, 'research_more')"
                      >
                        补充检索
                      </button>
                      <button
                        v-if="actionAllowed(message, 'change_goal')"
                        type="button"
                        class="review-button review-quiet"
                        :disabled="message.reviewing"
                        @click="openReviewForm(message, 'change_goal')"
                      >
                        调整目标
                      </button>
                      <button
                        type="button"
                        class="review-button review-abandon"
                        :disabled="message.reviewing"
                        @click="abandonResearch(message)"
                      >
                        放弃本次研究
                      </button>
                    </div>

                    <form
                      v-if="message.pendingAction"
                      class="review-form"
                      @submit.prevent="submitReview(message)"
                    >
                      <label :for="`review-${message.id}`">
                        {{ REVIEW_ACTIONS[message.pendingAction].prompt }}
                      </label>
                      <textarea
                        :id="`review-${message.id}`"
                        v-model="message.feedback"
                        rows="3"
                        :placeholder="
                          REVIEW_ACTIONS[message.pendingAction].placeholder
                        "
                        :disabled="message.reviewing"
                      ></textarea>
                      <div class="review-form-footer">
                        <small>
                          {{
                            REVIEW_ACTIONS[message.pendingAction].required
                              ? '这项操作需要填写内容'
                              : '不填写时将补查更多最新报道与不同来源'
                          }}
                        </small>
                        <div>
                          <button
                            type="button"
                            class="form-cancel"
                            :disabled="message.reviewing"
                            @click="closeReviewForm(message)"
                          >
                            取消
                          </button>
                          <button
                            type="submit"
                            class="form-submit"
                            :disabled="
                              message.reviewing ||
                              (REVIEW_ACTIONS[message.pendingAction].required &&
                                !message.feedback.trim())
                            "
                          >
                            确认提交
                          </button>
                        </div>
                      </div>
                    </form>
                  </section>
                </section>

                <div
                  v-else
                  class="assistant-copy"
                  v-html="renderMessage(message.content)"
                ></div>
              </template>
            </article>
          </template>
        </div>

        <footer class="composer-area">
          <div
            v-if="pendingClarification && phase === 'idle'"
            class="clarification-context"
          >
            <div>
              <span>正在补充上一条请求</span>
              <p>{{ pendingClarification.originalMessage }}</p>
            </div>
            <button type="button" @click="cancelClarification">取消补充</button>
          </div>

          <form class="composer" @submit.prevent="send()">
            <label class="sr-only" for="ai-question">输入问题</label>
            <textarea
              id="ai-question"
              ref="inputEl"
              v-model="inputText"
              rows="1"
              :placeholder="inputPlaceholder"
              :disabled="interfaceLocked"
              @input="autoResize"
              @keydown="handleKeydown"
            ></textarea>
            <button
              type="submit"
              :disabled="!inputText.trim() || interfaceLocked"
            >
              <template v-if="phase === 'requesting'">
                <span class="button-ring" aria-hidden="true"></span>
                <span class="sr-only">正在处理</span>
              </template>
              <span v-else>{{ activeMode.action }}</span>
            </button>
          </form>

          <div class="composer-foot">
            <span v-if="phase === 'waiting_review'">
              当前研究已暂停，请在报告底部完成审核。
            </span>
            <span v-else-if="phase === 'reviewing'">
              正在恢复研究流程，请保持页面开启。
            </span>
            <span v-else>Enter 发送 · Shift + Enter 换行</span>
            <span>AI 可能出错，重要结论请核对来源</span>
          </div>
        </footer>
      </section>
    </section>
  </div>
</template>

<style scoped>
.ai-page {
  max-width: 1240px;
}

.ai-shell {
  height: clamp(620px, calc(100dvh - 160px), 900px);
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr);
  overflow: hidden;
  background: #faf9f5;
  border: 1px solid #d8d5cb;
  box-shadow: 0 18px 55px rgba(20, 20, 19, 0.08);
  animation: shell-in 0.45s ease both;
}

.mode-rail {
  min-width: 0;
  padding: 30px 24px 24px;
  display: flex;
  flex-direction: column;
  color: #faf9f5;
  background: #141413;
}

.rail-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: Poppins, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
}

.rail-mark,
.assistant-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  font-family: Georgia, serif;
  font-weight: 700;
}

.rail-mark {
  width: 30px;
  height: 30px;
  color: #141413;
  background: #d97757;
  border-radius: 50%;
}

.rail-intro {
  margin: 52px 0 34px;
}

.rail-eyebrow,
.workspace-kicker,
.welcome-number,
.research-head p,
.review-title p {
  font-family: Poppins, "PingFang SC", "Microsoft YaHei", sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.13em;
}

.rail-eyebrow {
  margin-bottom: 12px;
  color: #d97757;
  font-size: 10px;
  font-weight: 600;
}

.rail-intro h1 {
  max-width: 230px;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 27px;
  font-weight: 500;
  line-height: 1.34;
  letter-spacing: -0.025em;
}

.rail-intro > p:last-child {
  margin-top: 16px;
  color: #b0aea5;
  font-size: 12.5px;
  line-height: 1.75;
}

.mode-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.mode-option {
  width: 100%;
  padding: 13px 12px;
  display: grid;
  grid-template-columns: 25px minmax(0, 1fr);
  gap: 8px;
  color: #b0aea5;
  border: 1px solid transparent;
  border-radius: 4px;
  text-align: left;
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease;
}

.mode-option:hover:not(:disabled) {
  color: #faf9f5;
  border-color: rgba(250, 249, 245, 0.2);
}

.mode-option.active {
  color: #141413;
  background: #faf9f5;
  border-color: #faf9f5;
}

.mode-option:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.mode-index {
  padding-top: 2px;
  font-family: Poppins, sans-serif;
  font-size: 9px;
  letter-spacing: 0.08em;
  opacity: 0.7;
}

.mode-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.mode-copy strong {
  font-size: 13px;
  font-weight: 600;
}

.mode-copy small {
  font-size: 10.5px;
  line-height: 1.45;
  opacity: 0.72;
}

.rail-footer {
  margin-top: auto;
  padding-top: 24px;
  color: #b0aea5;
  border-top: 1px solid rgba(250, 249, 245, 0.13);
  font-size: 10.5px;
  line-height: 1.6;
}

.service-line {
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #faf9f5;
}

.service-dot {
  width: 7px;
  height: 7px;
  background: #788c5d;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(120, 140, 93, 0.18);
}

.conversation-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    linear-gradient(rgba(20, 20, 19, 0.025) 1px, transparent 1px),
    #faf9f5;
  background-size: 100% 38px;
}

.workspace-head {
  min-height: 76px;
  padding: 18px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: rgba(250, 249, 245, 0.95);
  border-bottom: 1px solid #e8e6dc;
}

.workspace-kicker {
  margin-bottom: 3px;
  color: #6f6c65;
  font-size: 10px;
  font-weight: 600;
}

.workspace-head h2 {
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 20px;
  font-weight: 500;
}

.clear-button {
  padding: 7px 0;
  color: #706d66;
  border-bottom: 1px solid transparent;
  font-size: 12px;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}

.clear-button:hover:not(:disabled) {
  color: #9d4b32;
  border-color: #d97757;
}

.clear-button:disabled {
  cursor: not-allowed;
  opacity: 0.38;
}

.conversation-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 42px clamp(26px, 5vw, 66px);
  scrollbar-color: #b0aea5 transparent;
}

.welcome {
  max-width: 720px;
  margin: 4vh auto 0;
}

.welcome-number {
  margin-bottom: 16px;
  color: #9d4b32;
  font-size: 10px;
  font-weight: 600;
}

.welcome h2 {
  max-width: 620px;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: clamp(34px, 5vw, 55px);
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.035em;
}

.welcome-description {
  max-width: 580px;
  margin-top: 18px;
  color: #6f6c65;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 15px;
  line-height: 1.8;
}

.suggestion-grid {
  margin-top: 42px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border-top: 1px solid #d8d5cb;
  border-left: 1px solid #d8d5cb;
}

.suggestion {
  min-height: 112px;
  padding: 16px 18px;
  display: grid;
  grid-template-columns: 25px minmax(0, 1fr) 16px;
  gap: 8px;
  color: #282724;
  background: rgba(250, 249, 245, 0.82);
  border-right: 1px solid #d8d5cb;
  border-bottom: 1px solid #d8d5cb;
  text-align: left;
  transition:
    background-color 0.18s ease,
    color 0.18s ease;
}

.suggestion > span {
  color: #9d4b32;
  font-family: Poppins, sans-serif;
  font-size: 9px;
  letter-spacing: 0.08em;
}

.suggestion strong {
  align-self: center;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.65;
}

.suggestion i {
  align-self: end;
  font-style: normal;
}

.suggestion:hover {
  color: #faf9f5;
  background: #141413;
}

.suggestion:hover > span {
  color: #d97757;
}

.message {
  max-width: 760px;
  margin: 0 auto 38px;
  animation: message-in 0.3s ease both;
}

.message-user {
  width: min(76%, 620px);
  margin-right: 0;
}

.message-research {
  max-width: 860px;
}

.user-meta,
.assistant-meta {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 9px;
  color: #6f6c65;
  font-family: Poppins, "PingFang SC", sans-serif;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.user-meta {
  justify-content: flex-end;
}

.user-meta span:first-child::after {
  margin-left: 9px;
  content: "·";
}

.user-copy {
  padding: 14px 17px;
  color: #282724;
  background: #f0ded5;
  border-left: 3px solid #d97757;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
}

.user-copy,
.assistant-copy,
.report-paper,
.report-paper :deep(a),
.report-paper :deep(code) {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.assistant-mark {
  width: 24px;
  height: 24px;
  color: #faf9f5;
  background: #141413;
  border-radius: 50%;
  font-size: 11px;
}

.assistant-copy {
  padding-left: 33px;
  color: #282724;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 15px;
  line-height: 1.9;
}

.assistant-copy :deep(a),
.report-paper :deep(a) {
  color: #8e432f;
  text-decoration: underline;
  text-decoration-color: rgba(142, 67, 47, 0.35);
  text-underline-offset: 3px;
}

.assistant-copy :deep(code),
.report-paper :deep(code) {
  padding: 1px 5px;
  background: #e8e6dc;
  border-radius: 3px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.86em;
}

.assistant-copy :deep(.source-mark),
.report-paper :deep(.source-mark) {
  color: #8e432f;
  font-family: Poppins, sans-serif;
  font-size: 0.82em;
  font-weight: 600;
}

.loading-state,
.error-state,
.clarification-card {
  margin-left: 33px;
}

.loading-state {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  background: #f0eee7;
  border: 1px solid #dfddd3;
}

.loading-state strong {
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 14px;
  font-weight: 500;
}

.loading-state p {
  margin-top: 3px;
  color: #77746c;
  font-size: 11px;
}

.loading-ring,
.button-ring {
  display: inline-block;
  border-style: solid;
  border-radius: 50%;
  animation: spin 0.85s linear infinite;
}

.loading-ring {
  width: 22px;
  height: 22px;
  border-width: 2px;
  border-color: #b0aea5;
  border-top-color: #9d4b32;
}

.button-ring {
  width: 15px;
  height: 15px;
  border-width: 1.5px;
  border-color: rgba(250, 249, 245, 0.4);
  border-top-color: #faf9f5;
}

.error-state {
  padding: 16px 18px;
  color: #743625;
  background: #f6e5df;
  border-left: 3px solid #9d4b32;
}

.error-state strong {
  font-size: 13px;
}

.error-state p {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.65;
}

.clarification-card {
  padding: 17px 20px;
  color: #282724;
  background: #f2eee3;
  border-left: 3px solid #6a9bcc;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 14px;
  line-height: 1.8;
}

.clarification-label {
  margin-bottom: 5px;
  color: #527da6;
  font-family: Poppins, "PingFang SC", sans-serif;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.research-card {
  margin-top: 3px;
  background: #f7f5ef;
  border: 1px solid #d4d1c6;
  box-shadow: 0 12px 32px rgba(20, 20, 19, 0.06);
}

.research-card.completed {
  border-top: 3px solid #788c5d;
}

.research-card.abandoned {
  border-top: 3px solid #b0aea5;
}

.research-head {
  padding: 22px 25px 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  border-bottom: 1px solid #dedbd1;
}

.research-head p {
  margin-bottom: 5px;
  color: #9d4b32;
  font-size: 9px;
  font-weight: 600;
}

.research-head h3 {
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 20px;
  font-weight: 500;
}

.status-tag {
  padding: 5px 9px;
  color: #8e432f;
  background: #f0ded5;
  border: 1px solid #dfb8a9;
  font-size: 10px;
  font-weight: 600;
}

.status-tag.final {
  color: #50613d;
  background: #e8ecdf;
  border-color: #c9d2bb;
}

.status-tag.closed {
  color: #66635d;
  background: #e8e6dc;
  border-color: #cbc8bd;
}

.research-facts {
  padding: 11px 25px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  color: #6f6c65;
  background: #eeece5;
  border-bottom: 1px solid #dedbd1;
  font-size: 10.5px;
}

.research-facts span:not(:last-child)::before {
  margin-right: 6px;
  color: #d97757;
  content: "•";
}

.revision-note {
  margin: 16px 25px 0;
  padding: 9px 12px;
  color: #50613d;
  background: #e8ecdf;
  border-left: 2px solid #788c5d;
  font-size: 11px;
}

.report-paper {
  padding: 34px clamp(24px, 5vw, 54px) 42px;
  color: #282724;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 14px;
  line-height: 1.92;
}

.report-paper > p {
  margin: 0 0 13px;
}

.report-heading {
  color: #141413;
  font-family: Poppins, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-weight: 600;
  line-height: 1.35;
}

.report-heading-1 {
  margin: 0 0 26px;
  padding-bottom: 18px;
  border-bottom: 2px solid #141413;
  font-size: 25px;
}

.report-heading-2 {
  margin: 30px 0 13px;
  font-size: 17px;
}

.report-heading-3 {
  margin: 22px 0 9px;
  color: #5b5851;
  font-size: 14px;
}

.report-list {
  margin: 8px 0 18px;
  padding-left: 22px;
}

.report-list li {
  margin-bottom: 7px;
  padding-left: 3px;
}

.report-paper blockquote {
  margin: 18px 0;
  padding: 9px 16px;
  color: #5f5c55;
  border-left: 3px solid #d97757;
}

.review-panel {
  padding: 22px 25px 25px;
  background: #e8e6dc;
  border-top: 1px solid #d4d1c6;
}

.review-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.review-title p {
  margin-bottom: 4px;
  color: #8e432f;
  font-size: 9px;
  font-weight: 600;
}

.review-title h4 {
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 16px;
  font-weight: 500;
}

.review-title > span {
  color: #706d66;
  font-size: 10px;
}

.review-actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.review-button,
.form-cancel,
.form-submit {
  padding: 8px 13px;
  border: 1px solid #aaa79e;
  font-size: 11px;
  font-weight: 600;
  transition:
    color 0.15s ease,
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.review-button {
  color: #383733;
  background: transparent;
}

.review-button:hover:not(:disabled) {
  border-color: #8e432f;
  color: #8e432f;
}

.review-primary {
  color: #faf9f5;
  background: #141413;
  border-color: #141413;
}

.review-primary:hover:not(:disabled) {
  color: #faf9f5;
  background: #383733;
  border-color: #383733;
}

.review-quiet {
  border-color: transparent;
}

.review-abandon {
  margin-left: auto;
  color: #77746c;
  border-color: transparent;
}

.review-button:disabled,
.form-cancel:disabled,
.form-submit:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.review-form {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #cbc8bd;
}

.review-form label {
  display: block;
  margin-bottom: 7px;
  color: #383733;
  font-size: 11px;
  font-weight: 600;
}

.review-form textarea {
  width: 100%;
  min-height: 86px;
  padding: 11px 13px;
  resize: vertical;
  color: #282724;
  background: #faf9f5;
  border: 1px solid #bcb9af;
  border-radius: 0;
  outline: none;
  font-size: 12px;
  line-height: 1.6;
}

.review-form textarea:focus {
  border-color: #8e432f;
  box-shadow: 0 0 0 2px rgba(217, 119, 87, 0.18);
}

.review-form-footer {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.review-form-footer small {
  color: #77746c;
  font-size: 9.5px;
}

.review-form-footer > div {
  display: flex;
  gap: 7px;
}

.form-cancel {
  color: #5f5c55;
}

.form-submit {
  color: #faf9f5;
  background: #8e432f;
  border-color: #8e432f;
}

.clarification-context {
  padding: 11px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  background: #edf2f6;
  border-top: 1px solid #ccd9e5;
}

.clarification-context > div {
  min-width: 0;
}

.clarification-context span {
  color: #527da6;
  font-size: 10px;
  font-weight: 600;
}

.clarification-context p {
  max-width: 620px;
  overflow: hidden;
  color: #5f5c55;
  font-size: 10.5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clarification-context button {
  flex: 0 0 auto;
  color: #527da6;
  font-size: 10.5px;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.composer-area {
  background: #faf9f5;
  border-top: 1px solid #d8d5cb;
}

.composer {
  padding: 16px 22px 9px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 10px;
}

.composer textarea {
  width: 100%;
  min-height: 46px;
  max-height: 160px;
  padding: 12px 14px;
  resize: none;
  color: #282724;
  background: transparent;
  border: 1px solid #bdbab0;
  border-radius: 0;
  outline: none;
  font-family: Lora, "Songti SC", STSong, Georgia, serif;
  font-size: 13px;
  line-height: 1.65;
}

.composer textarea:focus {
  border-color: #8e432f;
  box-shadow: inset 3px 0 #d97757;
}

.composer textarea:disabled {
  color: #96938a;
  background: #eeece5;
  cursor: not-allowed;
}

.composer > button {
  min-width: 104px;
  min-height: 46px;
  padding: 10px 16px;
  color: #faf9f5;
  background: #141413;
  border: 1px solid #141413;
  font-size: 11.5px;
  font-weight: 600;
  transition:
    background-color 0.15s ease,
    opacity 0.15s ease;
}

.composer > button:hover:not(:disabled) {
  background: #383733;
}

.composer > button:disabled {
  cursor: not-allowed;
  opacity: 0.42;
}

.composer-foot {
  padding: 0 23px 13px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #6f6c65;
  font-size: 11px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

button:focus-visible,
textarea:focus-visible {
  outline: 2px solid #6a9bcc;
  outline-offset: 3px;
}

@keyframes shell-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 880px) {
  .ai-shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    height: max(720px, calc(100dvh - 130px));
  }

  .mode-rail {
    padding: 20px;
  }

  .rail-intro {
    margin: 28px 0 20px;
  }

  .rail-intro h1 {
    max-width: 600px;
    font-size: 24px;
  }

  .rail-intro > p:last-child {
    max-width: 680px;
  }

  .mode-list {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .mode-option {
    min-height: 86px;
  }

  .rail-footer {
    display: none;
  }

}

@media (max-width: 640px) {
  .ai-page {
    padding: 0 12px;
  }

  .ai-shell {
    height: max(720px, calc(100dvh - 130px));
  }

  .mode-rail {
    padding: 14px 16px 16px;
  }

  .rail-intro {
    display: none;
  }

  .mode-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-top: 14px;
  }

  .mode-option {
    min-height: auto;
    padding: 9px 5px;
    display: block;
    text-align: center;
  }

  .mode-index,
  .mode-copy small {
    display: none;
  }

  .workspace-head {
    min-height: 66px;
    padding: 14px 18px;
  }

  .conversation-body {
    padding: 30px 18px;
  }

  .welcome {
    margin-top: 0;
  }

  .welcome h2 {
    font-size: 34px;
  }

  .suggestion-grid {
    grid-template-columns: 1fr;
    margin-top: 30px;
  }

  .suggestion {
    min-height: 86px;
  }

  .message,
  .message-user {
    width: 100%;
  }

  .assistant-copy,
  .loading-state,
  .error-state,
  .clarification-card {
    margin-left: 0;
    padding-left: 15px;
  }

  .research-head,
  .review-title,
  .review-form-footer {
    flex-direction: column;
  }

  .research-head,
  .review-panel {
    padding-left: 18px;
    padding-right: 18px;
  }

  .research-facts {
    padding-left: 18px;
    padding-right: 18px;
  }

  .report-paper {
    padding: 28px 18px 34px;
  }

  .review-form-footer {
    align-items: flex-start;
  }

  .composer {
    padding: 12px 14px 8px;
    grid-template-columns: 1fr;
  }

  .composer > button {
    width: 100%;
  }

  .composer-foot {
    padding: 0 14px 12px;
    flex-direction: column;
    gap: 2px;
  }

  .clarification-context {
    align-items: flex-start;
    flex-wrap: wrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ai-shell,
  .message,
  .loading-ring,
  .button-ring {
    animation: none;
  }
}
</style>
