<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const buildTime = ref(new Date(__BUILD_TIME__).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }))

const route = useRoute()
</script>

<template>
  <header class="header">
    <div class="site-brand">
      <img src="/rabbit.png" alt="logo" class="logo" />
      <span class="site-name">投资小兔兔</span>
    </div>
    <nav class="tabs">
      <router-link to="/" :class="{ active: route.path === '/' }">表格</router-link>
      <router-link to="/grid" :class="{ active: route.path.startsWith('/grid') }">网格</router-link>
    </nav>
    <a href="https://github.com/geektutu/investment" target="_blank" class="github-link">GitHub</a>
  </header>
  <router-view></router-view>
  <footer class="footer">
    构建时间：{{ buildTime }}
  </footer>
</template>
