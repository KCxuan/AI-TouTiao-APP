<script setup>
import { reactive, ref, onMounted } from 'vue'
import { updateUserInfo, changePassword } from '../api/user'
import { useUserStore } from '../stores/user'
import { toast } from '../composables/toast'
import { genderLabel } from '../utils/format'

const userStore = useUserStore()

// ===== 资料编辑表单 =====
const profileForm = reactive({
  nickname: '',
  avatar: '',
  gender: 'unknown',
  bio: '',
  phone: ''
})
const savingProfile = ref(false)
const profileError = ref('')

// ===== 修改密码表单 =====
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const savingPassword = ref(false)
const passwordError = ref('')

onMounted(() => {
  // 打开页面时拉取最新信息（同时验证 token 有效性）
  userStore
    .refreshUserInfo()
    .then((info) => {
      fillForm(info)
    })
    .catch((e) => {
      toast(e.message, 'error')
      // 读取失败时回退到本地缓存
      if (userStore.userInfo) fillForm(userStore.userInfo)
    })
})

function fillForm(info) {
  profileForm.nickname = info.nickname || ''
  profileForm.avatar = info.avatar || ''
  profileForm.gender = info.gender || 'unknown'
  profileForm.bio = info.bio || ''
  profileForm.phone = info.phone || ''
}

async function handleSaveProfile() {
  profileError.value = ''
  if (profileForm.phone && !/^\d{6,15}$/.test(profileForm.phone)) {
    profileError.value = '手机号格式不正确'
    return
  }
  savingProfile.value = true
  try {
    const body = await updateUserInfo({ ...profileForm })
    userStore.setAuth(userStore.token, body.data)
    toast(body.message || '资料更新成功', 'success')
  } catch (e) {
    profileError.value = e.message
  } finally {
    savingProfile.value = false
  }
}

async function handleChangePassword() {
  passwordError.value = ''
  if (!passwordForm.oldPassword || !passwordForm.newPassword) {
    passwordError.value = '请填写旧密码和新密码'
    return
  }
  if (passwordForm.newPassword.length < 6) {
    passwordError.value = '新密码至少 6 位'
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  savingPassword.value = true
  try {
    const body = await changePassword(
      passwordForm.oldPassword,
      passwordForm.newPassword
    )
    toast(body.message || '密码修改成功', 'success')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (e) {
    passwordError.value = e.message
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="container profile-page">
    <h1 class="page-title">个人中心</h1>

    <div class="profile-grid">
      <!-- 左侧：账号概览 -->
      <div class="card overview-card">
        <div class="avatar-preview">
          <img
            v-if="profileForm.avatar"
            :src="profileForm.avatar"
            alt="头像"
            @error="profileForm.avatar = ''"
          />
          <div v-else class="avatar-placeholder">
            {{ (userStore.displayName || '?').charAt(0).toUpperCase() }}
          </div>
        </div>
        <div class="overview-name">{{ userStore.displayName || '未命名用户' }}</div>
        <div class="overview-username">@{{ userStore.userInfo?.username }}</div>
        <div class="overview-tag">性别：{{ genderLabel(profileForm.gender) }}</div>
        <p class="overview-bio">{{ profileForm.bio || '这个人很懒，什么都没留下' }}</p>
      </div>

      <div class="profile-column">
        <!-- 编辑资料 -->
        <div class="card form-card">
          <h2 class="form-title">编辑资料</h2>
          <form @submit.prevent="handleSaveProfile">
            <div class="field">
              <label for="nickname">昵称</label>
              <input
                id="nickname"
                v-model="profileForm.nickname"
                type="text"
                placeholder="不超过 50 个字符"
                maxlength="50"
              />
            </div>

            <div class="field">
              <label for="avatar">头像 URL</label>
              <input
                id="avatar"
                v-model="profileForm.avatar"
                type="text"
                placeholder="https://…（图片链接）"
                maxlength="255"
              />
            </div>

            <div class="field">
              <label for="gender">性别</label>
              <select id="gender" v-model="profileForm.gender">
                <option value="unknown">保密</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </div>

            <div class="field">
              <label for="phone">手机号</label>
              <input
                id="phone"
                v-model="profileForm.phone"
                type="text"
                placeholder="选填"
                maxlength="15"
              />
            </div>

            <div class="field">
              <label for="bio">个人简介</label>
              <textarea
                id="bio"
                v-model="profileForm.bio"
                placeholder="介绍一下自己吧…"
                maxlength="500"
              ></textarea>
            </div>

            <p v-if="profileError" class="error-msg">{{ profileError }}</p>

            <button type="submit" class="btn btn-primary" :disabled="savingProfile">
              {{ savingProfile ? '保存中…' : '保存资料' }}
            </button>
          </form>
        </div>

        <!-- 修改密码 -->
        <div class="card form-card">
          <h2 class="form-title">修改密码</h2>
          <form @submit.prevent="handleChangePassword">
            <div class="field">
              <label for="oldPassword">当前密码</label>
              <input
                id="oldPassword"
                v-model="passwordForm.oldPassword"
                type="password"
                autocomplete="current-password"
              />
            </div>

            <div class="field">
              <label for="newPassword">新密码</label>
              <input
                id="newPassword"
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="至少 6 位"
                autocomplete="new-password"
              />
            </div>

            <div class="field">
              <label for="confirmNewPassword">确认新密码</label>
              <input
                id="confirmNewPassword"
                v-model="passwordForm.confirmPassword"
                type="password"
                autocomplete="new-password"
              />
            </div>

            <p v-if="passwordError" class="error-msg">{{ passwordError }}</p>

            <button type="submit" class="btn btn-outline" :disabled="savingPassword">
              {{ savingPassword ? '提交中…' : '修改密码' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.profile-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  align-items: start;
}

/* 账号概览 */
.overview-card {
  padding: 32px 24px;
  text-align: center;
  position: sticky;
  top: 88px;
}

.avatar-preview {
  width: 88px;
  height: 88px;
  margin: 0 auto 14px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--border-strong);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent-soft);
  color: var(--accent-hover);
  font-family: var(--font-serif);
  font-size: 34px;
  font-weight: 700;
}

.overview-name {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
}

.overview-username {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.overview-tag {
  display: inline-block;
  font-size: 12px;
  color: var(--accent-hover);
  background-color: var(--accent-soft);
  border-radius: 999px;
  padding: 3px 12px;
  margin-bottom: 14px;
}

.overview-bio {
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.7;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

/* 表单区 */
.profile-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-card {
  padding: 28px 32px;
}

.form-title {
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 600;
  margin-bottom: 20px;
}

.error-msg {
  background-color: var(--error-soft);
  color: var(--error);
  font-size: 13px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
}

@media (max-width: 860px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .overview-card {
    position: static;
  }
}
</style>
