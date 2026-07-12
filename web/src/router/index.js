import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'

const baseUrl = import.meta.env.VITE_BASE_URL || '/'

// Add redirects for parent routes
routes.forEach(route => {
  if (route.path === '/' && route.children?.length) {
    route.children.unshift({ path: '', redirect: '/atr' })
  }
  if (route.path === '/grid' && route.children?.length) {
    route.children.unshift({ path: '', redirect: '/grid/calculator' })
  }
})

const router = createRouter({
  history: createWebHistory(baseUrl),
  routes,
})

export default router
