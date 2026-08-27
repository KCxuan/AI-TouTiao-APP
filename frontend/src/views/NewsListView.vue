<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCategories, getNewsList, searchNews } from '../api/news'
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

const keywordInput = ref('')
const activeKeyword = ref('')
const onlyCurrentCategory = ref(false)
const isSearchMode = computed(() => activeKeyword.value.length > 0)

function searchCategoryId() {
  return onlyCurrentCategory.value ? activeCategoryId.value : null
}

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
  if (isSearchMode.value) {
    await loadSearch()
    return
  }
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

async function loadSearch() {
  if (!activeKeyword.value) return
  listError.value = ''
  loadingList.value = true
  try {
    page.value = 1
    const body = await searchNews(
      activeKeyword.value,
      1,
      PAGE_SIZE,
      searchCategoryId()
    )
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

async function handleSearch() {
  const keyword = keywordInput.value.trim()
  if (!keyword) {
    toast('请输入搜索关键词', 'error')
    return
  }
  activeKeyword.value = keyword
  await loadSearch()
}

function clearSearch() {
  keywordInput.value = ''
  activeKeyword.value = ''
  loadList()
}

function handleScopeChange() {
  if (isSearchMode.value) {
    loadSearch()
  }
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  loadingMore.value = true
  try {
    const nextPage = page.value + 1
    const body = isSearchMode.value
      ? await searchNews(
          activeKeyword.value,
          nextPage,
          PAGE_SIZE,
          searchCategoryId()
        )
      : await getNewsList(activeCategoryId.value, nextPage, PAGE_SIZE)
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
  if (isSearchMode.value && onlyCurrentCategory.value) {
    await loadSearch()
    return
  }
  if (!isSearchMode.value) {
    await loadList()
  }
}

function newsImage(item) {
  return pick(item, 'image')
}
</script>

<template>
  <div class="container">
    <form class="search-bar" @submit.prevent="handleSearch">
      <input
        v-model="keywordInput"
        class="search-input"
        type="search"
        maxlength="50"
        placeholder="搜索新闻标题或简介"
        aria-label="搜索新闻"
      />
      <button class="btn btn-primary" type="submit" :disabled="loadingList">
        搜索
      </button>
      <button
        v-if="isSearchMode"
        class="btn btn-outline"
        type="button"
        @click="clearSearch"
      >
        清除
      </button>
      <label class="search-scope">
        <input v-model="onlyCurrentCategory" type="checkbox" @change="handleScopeChange" />
        仅当前分类
      </label>
    </form>

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
      <p>{{ isSearchMode ? '正在搜索…' : '正在加载新闻列表…' }}</p>
    </div>

    <div v-else-if="listError" class="card placeholder-card">
      <div class="placeholder-icon">⚠️</div>
      <h3>加载失败</h3>
      <p>{{ listError }}</p>
    </div>

    <div v-else-if="newsList.length === 0" class="card placeholder-card">
      <div class="placeholder-icon">🗞️</div>
      <h3>{{ isSearchMode ? '没有找到相关新闻' : '该分类下暂无新闻' }}</h3>
      <p v-if="isSearchMode">试试更短的关键词，或取消「仅当前分类」</p>
      <p v-else>可以去其他分类看看，或在 news 表中添加数据</p>
    </div>

    <template v-else>
      <div class="list-meta">
        <template v-if="isSearchMode">
          搜索「<strong>{{ activeKeyword }}</strong>」共 <strong>{{ total }}</strong> 条
        </template>
        <template v-else>
          共 <strong>{{ total }}</strong> 条新闻
        </template>
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
.search-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  min-width: 200px;
  height: 40px;
  padding: 0 14px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background-color: var(--surface-white);
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.search-scope {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
}

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
