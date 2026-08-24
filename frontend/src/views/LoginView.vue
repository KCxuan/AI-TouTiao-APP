<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { registerUser, loginUser } from '../api/user'
import { useUserStore } from '../stores/user'
import { toast } from '../composables/toast'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const mode = ref('login') // login | register
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

function switchMode(m) {
  mode.value = m
  errorMsg.value = ''
  form.password = ''
  form.confirmPassword = ''
}

function validate() {
  if (form.username.trim().length < 3) {
    errorMsg.value = '用户名至少 3 个字符（后端限制 3-20）'
    return false
  }
  if (form.password.length < 6) {
    errorMsg.value = '密码至少 6 位（后端限制 6-100）'
    return false
  }
  if (mode.value === 'register' && form.password !== form.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return false
  }
  return true
}

async function handleSubmit() {
  errorMsg.value = ''
  if (!validate()) return

  loading.value = true
  try {
    let body
    if (mode.value === 'login') {
      body = await loginUser({
        username: form.username.trim(),
        password: form.password
      })
    } else {
      body = await registerUser({
        username: form.username.trim(),
        password: form.password
      })
    }
    // data: { token, userInfo }
    userStore.setAuth(body.data.token, body.data.userInfo)
    toast(body.message || (mode.value === 'login' ? '登录成功' : '注册成功'), 'success')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-head">
        <div class="logo-mark">头</div>
        <h1 class="login-title">欢迎来到头条新闻</h1>
        <p class="login-sub">登录后可体验收藏、浏览历史等完整功能</p>
      </div>

      <div class="tabs">
        <button
          class="tab"
          :class="{ active: mode === 'login' }"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          class="tab"
          :class="{ active: mode === 'register' }"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="field">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="3-20 个字符"
            autocomplete="username"
          />
        </div>

        <div class="field">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="至少 6 位"
            autocomplete="current-password"
          />
        </div>

        <div v-if="mode === 'register'" class="field">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
          {{ loading ? '请稍候…' : mode === 'login' ? '登录' : '注册并登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 220px);
  padding: 32px 0;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 40px 36px;
}

.login-head {
  text-align: center;
  margin-bottom: 28px;
}

.logo-mark {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  border-radius: var(--radius-md);
}

.login-title {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 6px;
}

.login-sub {
  font-size: 13px;
  color: var(--text-secondary);
}

.tabs {
  display: flex;
  background-color: var(--bg);
  border-radius: var(--radius-sm);
  padding: 4px;
  margin-bottom: 24px;
}

.tab {
  flex: 1;
  padding: 8px 0;
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.tab.active {
  background-color: var(--surface-white);
  color: var(--text-primary);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.error-msg {
  background-color: var(--error-soft);
  color: var(--error);
  font-size: 13px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
}

.submit-btn {
  width: 100%;
  padding: 12px 0;
  font-size: 15px;
  margin-top: 4px;
}
</style>
