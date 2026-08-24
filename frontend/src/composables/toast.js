import { reactive } from 'vue'

// 极简全局 Toast，避免引入组件库
let seed = 0
const toasts = reactive([])

export function toast(message, type = 'info') {
  const id = ++seed
  toasts.push({ id, message, type })
  setTimeout(() => {
    const idx = toasts.findIndex((t) => t.id === id)
    if (idx !== -1) toasts.splice(idx, 1)
  }, 3000)
}

export function useToasts() {
  return toasts
}
