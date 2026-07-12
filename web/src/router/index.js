import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'

const baseUrl = import.meta.env.VITE_BASE_URL || '/'

const router = createRouter({
  history: createWebHistory(baseUrl),
  routes,
})

export default router
