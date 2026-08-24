<script setup>
import { ref, onMounted } from 'vue'
import { getCategories, getNewsList } from '../api/news'
import { pick, formatTime, formatViews } from '../utils/format'
import { toast } from '../composables/toast'

const PAGE_SIZE = 10

const categories = ref([])
const activeCategoryId = ref(null)
const newsList = ref([])
const total = ref(0)
const hasMore = ref(false)
const page = ref(1)

const loadingCategories = ref(false)
const loadingList = ref(false)
const loadingMore = ref(false)
const listError = ref('')

onMounted(async () => {
  loadingCategories.value = true
  try {
    const body = await getCategories()
    categories.value = body.data || []
    if (categories.value.length > 0) {
      activeCategoryId.value = categories.value[0].id
      await loadList()
    }
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loadingCategories.value = false
  }
})

async function loadList() {
  if (activeCategoryId.value === null) return
  listError.value = ''
  loadingList.value = true
  try {
    page.value = 1
    const body = await getNewsList(activeCategoryId.value, 1, PAGE_SIZE)
    const data = body.data || {}
    newsList.value = data.list || []
    total.value = data.total || 0
    hasMore.value = !!data.hasMore
  } catch (e) {
    listError.value = e.message
    newsList.value = []
  } finally {
    loadingList.value = false
  }
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true
  try {
    const nextPage = page.value + 1
    const body = await getNewsList(activeCategoryId.value, nextPage, PAGE_SIZE)
    const data = body.data || {}
    newsList.value.push(...(data.list || []))
    page.value = nextPage
    hasMore.value = !!data.hasMore
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loadingMore.value = false
  }
}

async function switchCategory(id) {
  if (id === activeCategoryId.value) return
  activeCategoryId.value = id
  await loadList()
}

function newsImage(item) {
  return pick(item, 'image')
}
</script>

<template>
  <div class="container">
    <!-- 分类 Tab -->
    <div class="category-bar">
      <div v-if="loadingCategories" class="loading-block" style="padding: 16px 0">
        <span class="loading-spinner"></span>
        <p>正在加载分类…</p>
      </div>
      <div v-else-if="categories.length === 0" class="category-empty">
        暂无新闻分类数据，请先在数据库 news_category 表中插入分类
      </div>
      <template v-else>
        <div class="category-tabs">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="category-tab"
            :class="{ active: cat.id === activeCategoryId }"
            @click="switchCategory(cat.id)"
          >
            {{ cat.name }}
          </button>
        </div>
      </template>
    </div>

    <!-- 新闻列表 -->
    <div v-if="loadingList" class="loading-block card">
      <span class="loading-spinner"></span>
      <p>正在加载新闻列表…</p>
    </div>

    <div v-else-if="listError" class="card placeholder-card">
      <div class="placeholder-icon">⚠️</div>
      <h3>加载失败</h3>
      <p>{{ listError }}</p>
    </div>

    <div v-else-if="newsList.length === 0" class="card placeholder-card">
      <div class="placeholder-icon">🗞️</div>
      <h3>该分类下暂无新闻</h3>
      <p>可以去其他分类看看，或在 news 表中添加数据</p>
    </div>

    <template v-else>
      <div class="list-meta">
        共 <strong>{{ total }}</strong> 条新闻
      </div>

      <div class="news-list">
        <RouterLink
          v-for="item in newsList"
          :key="item.id"
          :to="`/news/${item.id}`"
          class="news-item card"
        >
          <div class="news-body">
            <h2 class="news-title">{{ item.title }}</h2>
            <p class="news-desc">{{ item.description || '暂无简介' }}</p>
            <div class="news-meta">
              <span v-if="pick(item, 'author')">✍ {{ pick(item, 'author') }}</span>
              <span>🕒 {{ formatTime(pick(item, 'publishTime', 'publish_time')) }}</span>
              <span>👁 {{ formatViews(item.views) }} 次浏览</span>
            </div>
          </div>
          <img
            v-if="newsImage(item)"
            :src="newsImage(item)"
            alt="封面"
            class="news-thumb"
            loading="lazy"
          />
        </RouterLink>
      </div>

      <div class="load-more-wrap">
        <button
          v-if="hasMore"
          class="btn btn-outline load-more-btn"
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
.category-bar {
  margin-bottom: 20px;
}

.category-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
  background-color: var(--surface);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
}

.category-tabs {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.category-tab {
  padding: 8px 18px;
  border-radius: 999px;
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.category-tab:hover {
  color: var(--text-primary);
  background-color: var(--surface);
}

.category-tab.active {
  color: var(--accent);
  font-weight: 600;
  background-color: var(--surface-white);
  border-color: var(--accent);
}

.list-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.news-item {
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease,
    transform 0.15s ease;
}

.news-item:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.news-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.news-title {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
  line-height: 1.45;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-desc {
  font-size: 14px;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}

.news-meta {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12.5px;
  color: var(--text-tertiary);
}

.news-thumb {
  width: 160px;
  height: 106px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.load-more-wrap {
  text-align: center;
  margin-top: 28px;
}

.load-more-btn {
  min-width: 160px;
}

.no-more {
  color: var(--text-tertiary);
  font-size: 13px;
}

@media (max-width: 640px) {
  .news-item {
    flex-direction: column-reverse;
    gap: 12px;
  }

  .news-thumb {
    width: 100%;
    height: 160px;
  }
}
</style>
