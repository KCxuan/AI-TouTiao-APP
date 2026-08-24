import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端 CORS 白名单已放行 http://localhost:5173，保持默认端口即可
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '127.0.0.1'
  }
})
