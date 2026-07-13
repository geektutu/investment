<script setup>
const error = useError()
onMounted(() => {
  if (error.value?.statusCode === 404) {
    clearError({ redirect: '/' })
  }
})
</script>

<template>
  <div style="text-align: center; padding: 2rem;">
    <p>页面未找到，正在跳转首页...</p>
  </div>
</template>
