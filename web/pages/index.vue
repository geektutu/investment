<script setup>
const router = useRouter()
const route = useRoute()

const menuItems = [
  { path: '/atr', name: 'ETF ATR' },
  { path: '/stock-atr', name: '个股 ATR' },
]

// 处理 GitHub Pages 404 重定向
const redirectPath = localStorage.getItem('redirectPath')
if (redirectPath) {
  localStorage.removeItem('redirectPath')
  router.replace(redirectPath)
}

// 默认跳转到 /atr
if (route.path === '/') {
  router.replace('/atr')
}
</script>

<template>
  <div class="container">
    <h1>投资数据</h1>
    <div class="grid-layout">
      <aside class="sidebar">
        <ul class="menu">
          <li v-for="item in menuItems" :key="item.path">
            <NuxtLink :to="item.path" :class="{ active: $route.path === item.path }">
              {{ item.name }}
            </NuxtLink>
          </li>
        </ul>
      </aside>
      <main class="content">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>
