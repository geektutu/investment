<script setup>
const route = useRoute()
const baseURL = useRuntimeConfig().app.baseURL
const { buildTime } = useAppConfig()
</script>

<template>
  <div>
    <header class="header">
      <div class="site-brand">
        <img :src="`${baseURL}rabbit.png`" alt="logo" class="logo" />
        <span class="site-name">投资小兔兔</span>
      </div>
      <nav class="tabs">
  <NuxtLink to="/atr" :class="{ active: route.path.startsWith('/atr') || route.path.startsWith('/stock-atr') || route.path === '/' }">表格</NuxtLink>
  <NuxtLink to="/grid" :class="{ active: route.path.startsWith('/grid') }">网格</NuxtLink>
</nav>
      <a href="https://github.com/geektutu/investment" target="_blank" class="github-link">GitHub</a>
    </header>
    <slot />
    <footer class="footer">
      构建时间：{{ buildTime }}
    </footer>
  </div>
</template>
