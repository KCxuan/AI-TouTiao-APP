import { defineStore } from 'pinia'
import { getUserInfo } from '../api/user'

// 用户状态：token + userInfo，持久化到 localStorage
export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('toutiao_token') || '',
    userInfo: JSON.parse(localStorage.getItem('toutiao_user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    displayName: (state) => {
      const info = state.userInfo
      if (!info) return ''
      return info.nickname || info.username
    }
  },
  actions: {
    setAuth(token, userInfo) {
      this.token = token
      this.userInfo = userInfo
      localStorage.setItem('toutiao_token', token)
      localStorage.setItem('toutiao_user', JSON.stringify(userInfo))
    },
    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('toutiao_token')
      localStorage.removeItem('toutiao_user')
    },
    // 拉取最新用户信息（会话恢复或资料更新后调用）
    async refreshUserInfo() {
      const body = await getUserInfo()
      this.userInfo = body.data
      localStorage.setItem('toutiao_user', JSON.stringify(body.data))
      return body.data
    }
  }
})
