<script setup>
const router = useRouter()
const route = useRoute()

// 默认跳转到 /atr
if (route.path === '/') {
  router.replace('/atr')
}
</script>

<template>
  <div class="container">
    <NuxtPage />
  </div>
</template>
