import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  base: loadEnv(mode, process.cwd()).VITE_BASE_URL || '/',
  define: {
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
}))
