<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMyNewsList, deleteNews, getCategories } from '../api/news'
import { formatTime, formatViews } from '../utils/format'
import { toast } from '../composables/toast'

const PAGE_SIZE = 10

const router = useRouter()

const items = ref([])
const total = ref(0)
const hasMore = ref(false)
const page = ref(1)

const loadingMore = ref(false)
// 两种状态：normal 正常展示 / failed 加载失败
const pageState = ref('loading')
const errorMessage = ref('')

// 分类映射表：id -> name（用于展示分类名）
const categoryMap = ref({})

async function loadList() {
  pageState.value = 'loading'
  try {
    const body = await getMyNewsList(1, PAGE_SIZE)
    const data = body.data || {}
    items.value = data.list || []
    total.value = data.total || 0
    hasMore.value = !!data.hasMore
    page.value = 1
    pageState.value = 'normal'
  } catch (e) {
    errorMessage.value = e.message
    pageState.value = 'failed'
  }
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true
  try {
    const nextPage = page.value + 1
    const body = await getMyNewsList(nextPage, PAGE_SIZE)
    const data = body.data || {}
    items.value.push(...(data.list || []))
    page.value = nextPage
    hasMore.value = !!data.hasMore
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loadingMore.value = false
  }
}

// 编辑：把整条文章数据（含全部 ORM 字段）暂存到 sessionStorage 供编辑页回填，
// 再带 ?edit=<id> 跳转到发布页（发布页刷新时也能凭 id 回退拉取）
function handleEdit(item) {
  sessionStorage.setItem('toutiao_edit_news', JSON.stringify(item))
  router.push(`/publish?edit=${item.id}`)
}

// 删除：本地移除 + 失败回滚（与收藏页一致的交互模式）
async function handleDelete(item) {
  if (!window.confirm(`确定要删除「${item.title}」吗？删除后不可恢复。`)) return
  const snapshot = [...items.value]
  items.value = items.value.filter((i) => i.id !== item.id)
  total.value = Math.max(0, total.value - 1)
  try {
    const body = await deleteNews(item.id)
    toast(body.message || '删除成功')
  } catch (e) {
    items.value = snapshot
    total.value = snapshot.length > 0 ? total.value + 1 : 0
    toast(e.message, 'error')
  }
}

function categoryName(categoryId) {
  return categoryMap.value[categoryId] || `分类 ${categoryId}`
}

onMounted(async () => {
  // 分类名与列表并行加载
  getCategories()
    .then((body) => {
      const map = {}
      for (const cat of body.data || []) {
        map[cat.id] = cat.name
      }
      categoryMap.value = map
    })
    .catch(() => {})
  await loadList()
})
</script>

<template>
  <div class="container">
    <div class="page-head">
      <h1 class="page-title">我的发布</h1>
      <RouterLink to="/publish" class="btn btn-primary">+ 发布新闻</RouterLink>
    </div>

    <div v-if="pageState === 'loading'" class="loading-block card">
      <span class="loading-spinner"></span>
      <p>正在加载我的发布…</p>
    </div>

    <div v-else-if="pageState === 'failed'" class="card placeholder-card">
      <div class="placeholder-icon">⚠️</div>
      <h3>加载失败</h3>
      <p>{{ errorMessage }}</p>
      <button class="btn btn-outline" style="margin-top: 16px" @click="loadList">
        重新加载
      </button>
    </div>

    <div v-else-if="items.length === 0" class="card placeholder-card">
      <div class="placeholder-icon">📝</div>
      <h3>还没有发布过文章</h3>
      <p>写下第一篇新闻，让大家看到你的观点</p>
      <RouterLink to="/publish" class="btn btn-primary" style="margin-top: 16px">
        去发布
      </RouterLink>
    </div>

    <template v-else>
      <div class="list-meta">共 <strong>{{ total }}</strong> 篇文章</div>

      <div class="item-list">
        <div v-for="item in items" :key="item.id" class="card item-row">
          <RouterLink :to="`/news/${item.id}`" class="item-main">
            <div class="item-top">
              <span class="category-chip">{{ categoryName(item.category_id) }}</span>
              <span class="item-time">{{ formatTime(item.publish_time) }}</span>
            </div>
            <h2 class="item-title">{{ item.title }}</h2>
            <p class="item-desc">{{ item.description || '暂无简介' }}</p>
            <div class="item-meta">
              <span>👁 {{ formatViews(item.views) }} 浏览</span>
              <span v-if="item.image">🖼 有封面</span>
            </div>
          </RouterLink>
          <div class="item-actions">
            <button class="btn btn-outline action-btn" @click="handleEdit(item)">
              编辑
            </button>
            <button
              class="btn-danger-text action-btn"
              @click="handleDelete(item)"
            >
              删除
            </button>
          </div>
        </div>
      </div>

      <div class="load-more-wrap">
        <button
          v-if="hasMore"
          class="btn btn-outline"
          :disabled="loadingMore"
          @click="loadMore"
        >
          {{ loadingMore ? '加载中…' : '加载更多' }}
        </button>
        <p v-else class="no-more">— 已经到底啦 —</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.list-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-row {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 18px 22px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.item-row:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-md);
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.item-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.category-chip {
  font-size: 12px;
  color: var(--accent-hover);
  background-color: var(--accent-soft);
  border-radius: 999px;
  padding: 2px 10px;
}

.item-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.item-title {
  font-family: var(--font-serif);
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-desc {
  font-size: 13.5px;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.item-meta {
  margin-top: auto;
  display: flex;
  gap: 14px;
  font-size: 12.5px;
  color: var(--text-tertiary);
}

.item-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: stretch;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  min-width: 72px;
}

.load-more-wrap {
  text-align: center;
  margin-top: 24px;
}

.no-more {
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
