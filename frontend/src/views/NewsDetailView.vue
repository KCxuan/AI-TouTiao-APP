<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getNewsDetail } from '../api/news'
import { pick, formatTime, formatViews } from '../utils/format'
import { useUserStore } from '../stores/user'
import { toast } from '../composables/toast'
import { addHistory } from '../api/history'
import { checkFavorite, addFavorite, removeFavorite } from '../api/favorite'

const route = useRoute()
const userStore = useUserStore()

const detail = ref(null)
const relatedNews = ref([])
const loading = ref(false)
const loadError = ref('')

// 收藏状态
const isFavorite = ref(false)
const favoriteChecking = ref(false) // 初始状态查询中
const favoritePending = ref(false) // 收藏/取消请求中（防连点重复提交撞唯一约束）

async function loadDetail(id) {
  loading.value = true
  loadError.value = ''
  detail.value = null
  relatedNews.value = []
  try {
    const body = await getNewsDetail(id)
    detail.value = body.data
    relatedNews.value = body.data?.relatedNews || []
    // 登录状态下：上报浏览历史（失败静默，不打断阅读）+ 查询收藏状态
    if (userStore.isLoggedIn) {
      addHistory(Number(id)).catch(() => {})
      favoriteChecking.value = true
      // 归属校验：快速切换新闻时丢弃旧响应，避免污染当前页面的收藏星标
      const reqId = Number(id)
      checkFavorite(reqId)
        .then((res) => {
          if (reqId === Number(route.params.id)) {
            isFavorite.value = !!(res.data && res.data.isFavorite)
          }
        })
        .catch(() => {})
        .finally(() => {
          if (reqId === Number(route.params.id)) {
            favoriteChecking.value = false
          }
        })
    }
  } catch (e) {
    loadError.value = e.message
  } finally {
    loading.value = false
  }
}

// 切换相关新闻时复用同一路由组件，需要 watch 参数
watch(
  () => route.params.id,
  (newId) => {
    if (newId && route.name === 'news-detail') {
      isFavorite.value = false
      loadDetail(newId)
    }
  },
  { immediate: true }
)

async function toggleFavorite() {
  if (!userStore.isLoggedIn || favoritePending.value) return
  const newsId = Number(route.params.id)
  favoritePending.value = true
  try {
    if (isFavorite.value) {
      await removeFavorite(newsId)
      isFavorite.value = false
      toast('已取消收藏')
    } else {
      await addFavorite(newsId)
      isFavorite.value = true
      toast('收藏成功', 'success')
    }
  } catch (e) {
    toast(`收藏操作失败：${e.message}`, 'error')
  } finally {
    favoritePending.value = false
  }
}
</script>

<template>
  <div class="container detail-layout">
    <div v-if="loading" class="loading-block card">
      <span class="loading-spinner"></span>
      <p>正在加载新闻详情…</p>
    </div>

    <div v-else-if="loadError" class="card placeholder-card">
      <div class="placeholder-icon">🔍</div>
      <h3>无法加载新闻</h3>
      <p>{{ loadError }}</p>
      <RouterLink to="/" class="btn btn-outline" style="margin-top: 16px">
        返回首页
      </RouterLink>
    </div>

    <template v-else-if="detail">
      <article class="detail-main card">
        <img v-if="detail.image" :src="detail.image" alt="封面" class="detail-cover" />
        <h1 class="detail-title">{{ detail.title }}</h1>
        <div class="detail-meta">
          <span v-if="detail.author">作者：{{ detail.author }}</span>
          <span>发布时间：{{ formatTime(detail.publishTime) }}</span>
          <span>{{ formatViews(detail.views) }} 次浏览</span>
          <button
            v-if="userStore.isLoggedIn"
            class="fav-btn"
            :class="{ favored: isFavorite }"
            :disabled="favoriteChecking || favoritePending"
            @click="toggleFavorite"
          >
            {{ isFavorite ? '★ 已收藏' : '☆ 收藏' }}
          </button>
          <RouterLink v-else to="/login" class="fav-btn">☆ 登录后收藏</RouterLink>
        </div>
        <div class="divider"></div>
        <div class="detail-content">{{ detail.content }}</div>
      </article>

      <aside class="detail-aside">
        <div class="card aside-card">
          <h3 class="aside-title">相关阅读</h3>
          <p v-if="relatedNews.length === 0" class="aside-empty">
            暂无同分类的其他新闻
          </p>
          <RouterLink
            v-for="item in relatedNews"
            :key="item.id"
            :to="`/news/${item.id}`"
            class="aside-item"
          >
            <div class="aside-item-title">
              {{ pick(item, 'title') || item.title }}
            </div>
            <div class="aside-item-meta">
              <span>{{ formatTime(pick(item, 'publishTime', 'publish_time')) }}</span>
              <span>{{ formatViews(item.views) }} 浏览</span>
            </div>
          </RouterLink>
        </div>
      </aside>
    </template>
  </div>
</template>

<style scoped>
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 24px;
  align-items: start;
}

.detail-main {
  padding: 36px 40px;
}

.detail-cover {
  width: 100%;
  max-height: 380px;
  object-fit: cover;
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}

.detail-title {
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 700;
  line-height: 1.4;
  letter-spacing: -0.01em;
  margin-bottom: 16px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 18px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.fav-btn {
  margin-left: auto;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.fav-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.fav-btn.favored {
  background-color: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent-hover);
}

.divider {
  height: 1px;
  background-color: var(--border);
  margin: 22px 0;
}

.detail-content {
  font-size: 16px;
  line-height: 1.9;
  color: #2d2b27;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 侧栏 */
.aside-card {
  padding: 22px;
  position: sticky;
  top: 88px;
}

.aside-title {
  font-family: var(--font-serif);
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.aside-empty {
  font-size: 13px;
  color: var(--text-tertiary);
}

.aside-item {
  display: block;
  padding: 10px 0;
  border-bottom: 1px solid var(--bg);
}

.aside-item:last-child {
  border-bottom: none;
}

.aside-item-title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.15s ease;
}

.aside-item:hover .aside-item-title {
  color: var(--accent);
}

.aside-item-meta {
  margin-top: 4px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}

@media (max-width: 900px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-main {
    padding: 24px 20px;
  }
}
</style>
