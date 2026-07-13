<script setup>
const config = useRuntimeConfig()
const baseUrl = config.app.baseURL || '/'

// 保存当前路径到 localStorage 并跳转到首页
localStorage.setItem('redirectPath', window.location.pathname + window.location.search + window.location.hash)
window.location.href = baseUrl
</script>

<template>
  <p>Redirecting...</p>
</template>
