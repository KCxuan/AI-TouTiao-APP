<script setup>
import { ref, onMounted } from 'vue'
import {
  getFavoriteList,
  removeFavorite,
  clearFavorites
} from '../api/favorite'
import { formatTime, formatViews, timeAgo } from '../utils/format'
import { toast } from '../composables/toast'

const PAGE_SIZE = 10

const items = ref([])
const total = ref(0)
const hasMore = ref(false)
const page = ref(1)

const loadingMore = ref(false)
// 两种状态：normal 正常展示 / failed 加载失败
const pageState = ref('loading')
const errorMessage = ref('')

async function loadList() {
  pageState.value = 'loading'
  try {
    const body = await getFavoriteList(1, PAGE_SIZE)
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
    const body = await getFavoriteList(nextPage, PAGE_SIZE)
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

// 取消收藏（参数为新闻 ID，与 remove 接口的 newsId 对应）
// 本地移除 + 失败回滚，保留已加载的分页进度
async function handleRemove(newsId) {
  const snapshot = [...items.value]
  items.value = items.value.filter((i) => i.id !== newsId)
  total.value = Math.max(0, total.value - 1)
  try {
    const body = await removeFavorite(newsId)
    toast(body.message || '已取消收藏')
  } catch (e) {
    items.value = snapshot
    total.value = snapshot.length > 0 ? total.value + 1 : 0
    toast(e.message, 'error')
  }
}

async function handleClear() {
  if (!window.confirm('确定要清空所有收藏吗？此操作不可恢复。')) return
  try {
    const body = await clearFavorites()
    toast(body.message || '已清空收藏')
    items.value = []
    total.value = 0
    hasMore.value = false
    page.value = 1
  } catch (e) {
    toast(e.message, 'error')
  }
}

onMounted(loadList)
</script>

<template>
  <div class="container">
    <div class="page-head">
      <h1 class="page-title">我的收藏</h1>
      <button
        v-if="pageState === 'normal' && items.length > 0"
        class="btn btn-outline"
        @click="handleClear"
      >
        清空收藏
      </button>
    </div>

    <div v-if="pageState === 'loading'" class="loading-block card">
      <span class="loading-spinner"></span>
      <p>正在加载收藏列表…</p>
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
      <div class="placeholder-icon">☆</div>
      <h3>还没有收藏任何新闻</h3>
      <p>浏览新闻详情时点击"收藏"，即可在这里找到它们</p>
      <RouterLink to="/" class="btn btn-primary" style="margin-top: 16px">
        去逛逛
      </RouterLink>
    </div>

    <template v-else>
      <div class="list-meta">共 <strong>{{ total }}</strong> 条收藏</div>

      <div class="item-list">
        <div v-for="item in items" :key="item.favoriteId" class="card item-row">
          <RouterLink :to="`/news/${item.id}`" class="item-main">
            <h2 class="item-title">{{ item.title }}</h2>
            <p class="item-desc">{{ item.description || '暂无简介' }}</p>
            <div class="item-meta">
              <span v-if="item.author">✍ {{ item.author }}</span>
              <span>👁 {{ formatViews(item.views) }} 浏览</span>
              <span>发布于 {{ formatTime(item.publishTime) }}</span>
              <span class="fav-time">收藏于 {{ timeAgo(item.favoriteTime) }}</span>
            </div>
          </RouterLink>
          <div class="item-actions">
            <button
              class="btn-danger-text"
              @click="handleRemove(item.id)"
            >
              取消收藏
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
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12.5px;
  color: var(--text-tertiary);
}

.fav-time {
  color: var(--accent-hover);
}

.item-actions {
  display: flex;
  align-items: center;
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
