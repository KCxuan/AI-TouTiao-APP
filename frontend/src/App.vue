<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useToasts } from './composables/toast'

const router = useRouter()
const userStore = useUserStore()
const toasts = useToasts()

// 用户头像下拉菜单
const menuOpen = ref(false)
const menuRef = ref(null)

const avatarUrl = computed(() => userStore.userInfo?.avatar || '')
const initial = computed(() => {
  const name = userStore.displayName || userStore.userInfo?.username || ''
  return name ? name.charAt(0).toUpperCase() : '?'
})

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function handleClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    menuOpen.value = false
  }
}

function handleLogout() {
  menuOpen.value = false
  userStore.logout()
  router.push({ name: 'login' })
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <header class="navbar">
    <div class="container navbar-inner">
      <RouterLink to="/" class="logo">
        <span class="logo-mark">头</span>
        <span class="logo-text">头条新闻</span>
      </RouterLink>

      <nav class="nav-links">
        <RouterLink to="/" class="nav-link">首页</RouterLink>
        <RouterLink to="/publish" class="nav-link">发布</RouterLink>
        <RouterLink to="/mine" class="nav-link">我的发布</RouterLink>
        <RouterLink to="/favorites" class="nav-link">收藏</RouterLink>
        <RouterLink to="/history" class="nav-link">浏览历史</RouterLink>
        <RouterLink to="/ai" class="nav-link">AI 研究</RouterLink>
      </nav>

      <div class="nav-right">
        <template v-if="userStore.isLoggedIn">
          <div class="user-menu" ref="menuRef">
            <button
              class="avatar-btn"
              :title="userStore.displayName"
              aria-label="打开用户菜单"
              aria-haspopup="menu"
              :aria-expanded="menuOpen"
              @click="toggleMenu"
            >
              <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="avatar-img" />
              <span v-else class="avatar-fallback">{{ initial }}</span>
            </button>
            <Transition name="dropdown">
              <div v-if="menuOpen" class="dropdown">
                <div class="dropdown-header">
                  <div class="dropdown-name">{{ userStore.displayName }}</div>
                  <div class="dropdown-sub">@{{ userStore.userInfo?.username }}</div>
                </div>
                <RouterLink to="/profile" class="dropdown-item" @click="closeMenu">
                  个人中心
                </RouterLink>
                <button class="dropdown-item dropdown-item-btn" @click="handleLogout">
                  退出登录
                </button>
              </div>
            </Transition>
          </div>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-primary">登录 / 注册</RouterLink>
        </template>
      </div>
    </div>
  </header>

  <main class="page-main">
    <RouterView />
  </main>

  <footer class="footer">
    <div class="container">
      <p>头条新闻 · FastAPI + Vue 前后端联调演示</p>
    </div>
  </footer>

  <!-- 全局 Toast -->
  <div class="toast-wrap">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast-${t.type}`">
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--surface);
  border-bottom: 1px solid var(--border);
}

.navbar-inner {
  display: flex;
  align-items: center;
  gap: 32px;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-mark {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  border-radius: var(--radius-sm);
}

.logo-text {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.nav-links {
  display: flex;
  gap: 4px;
  flex: 1;
}

.nav-link {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
  transition: color 0.15s ease, background-color 0.15s ease;
}

.nav-link:hover {
  color: var(--text-primary);
  background-color: rgba(31, 30, 29, 0.04);
}

.nav-link.router-link-active {
  color: var(--accent);
  font-weight: 600;
}

.nav-right {
  display: flex;
  align-items: center;
}

/* 头像 */
.avatar-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  border: 1.5px solid var(--border-strong);
  transition: border-color 0.15s ease;
}

.avatar-btn:hover {
  border-color: var(--accent);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent-soft);
  color: var(--accent-hover);
  font-weight: 600;
  font-size: 15px;
}

/* 下拉菜单 */
.user-menu {
  position: relative;
}

.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  width: 200px;
  background-color: var(--surface-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.dropdown-header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--border);
}

.dropdown-name {
  font-weight: 600;
  font-size: 14px;
}

.dropdown-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--text-primary);
  transition: background-color 0.15s ease;
}

.dropdown-item:hover {
  background-color: var(--bg);
}

.dropdown-item-btn {
  color: var(--error);
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* 主体与页脚 */
.page-main {
  flex: 1;
  padding: 32px 0 64px;
}

.footer {
  border-top: 1px solid var(--border);
  padding: 20px 0;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: center;
}

/* Toast */
.toast-wrap {
  position: fixed;
  top: 76px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  pointer-events: none;
}

.toast {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--text-primary);
  color: var(--bg);
  font-size: 14px;
  box-shadow: var(--shadow-md);
  max-width: 90vw;
}

.toast-success {
  background-color: #3d5240;
}

.toast-error {
  background-color: var(--error);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 900px) {
  .navbar-inner {
    height: auto;
    min-height: 64px;
    padding-top: 12px;
    padding-bottom: 8px;
    flex-wrap: wrap;
    gap: 10px 14px;
  }

  .nav-links {
    order: 3;
    flex: 0 0 100%;
    width: 100%;
    padding-bottom: 2px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  .nav-link {
    flex: 0 0 auto;
    padding: 6px 11px;
    white-space: nowrap;
  }

  .nav-right {
    margin-left: auto;
  }

  .nav-right .btn {
    padding: 8px 13px;
    font-size: 12px;
  }

  .page-main {
    padding: 20px 0 40px;
  }
}

@media (max-width: 420px) {
  .logo-text {
    font-size: 18px;
  }
}
</style>
