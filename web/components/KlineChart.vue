<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  code: {
    type: String,
    required: true,
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])

const marketId = computed(() => {
  return /^(5|6|9|1[13])/.test(props.code) ? '1' : '0'
})

const iframeUrl = computed(
  () => `https://wap.eastmoney.com/quote/stock/${marketId.value}.${props.code}.html`,
)

const loading = ref(true)

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="kline-overlay" @click.self="emit('close')">
    <div class="kline-modal">
      <div class="kline-header">
        <h2>{{ name }} ({{ code }})</h2>
        <button class="kline-close" @click="emit('close')">✕</button>
      </div>
      <div class="kline-body">
        <div v-if="loading" class="kline-loading">加载中...</div>
        <iframe
          :src="iframeUrl"
          class="kline-frame"
          frameborder="0"
          scrolling="no"
          sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"
          referrerpolicy="no-referrer"
          @load="loading = false"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kline-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.kline-modal {
  background: var(--bg);
  border-radius: 12px;
  width: 90%;
  max-width: 1000px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.kline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.kline-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-h);
  margin: 0;
}

.kline-close {
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text);
  opacity: 0.6;
  padding: 4px 8px;
}

.kline-close:hover {
  opacity: 1;
}

.kline-body {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.kline-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text);
}

.kline-frame {
  width: 100%;
  height: calc(100% + 130px);
  border: none;
  display: block;
}

@media (prefers-color-scheme: dark) {
  .kline-modal {
    background: #1a1b26;
  }
}
</style>
