import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueRouter from 'vue-router/vite'

export default defineConfig(({ mode }) => ({
  plugins: [VueRouter(), vue()],
  base: loadEnv(mode, process.cwd()).VITE_BASE_URL || '/',
  define: {
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
}))
