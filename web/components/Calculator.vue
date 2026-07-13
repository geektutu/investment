<script setup>
import { ref, computed } from 'vue'

const basePrices = ref('')
const count = ref(5)
const gridSize = ref(20)

const inputPrices = computed(() => {
  return basePrices.value
    .split(',')
    .map(v => parseFloat(v.trim()))
    .filter(v => !isNaN(v))
})

const average = computed(() => {
  const prices = inputPrices.value
  if (prices.length === 0) return 0
  return prices.reduce((a, b) => a + b, 0) / prices.length
})

const result = computed(() => {
  const y = count.value
  const z = gridSize.value
  const x = average.value

  if (y <= 0 || z <= 0 || inputPrices.value.length === 0) return []

  const interval = z / y
  const prices = []
  for (let i = 0; i < y; i++) {
    prices.push(x - (y - 1) / 2 * interval + i * interval)
  }
  return prices
})

function formatPrice(val) {
  return val.toFixed(3)
}
</script>

<template>
  <div class="calculator">
    <div class="form-group">
      <label>网格基准价（逗号分隔）</label>
      <input v-model="basePrices" type="text" placeholder="如：100, 110, 105" />
      <span class="hint">已识别 {{ inputPrices.length }} 个价格，平均值：{{ formatPrice(average) }}</span>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>基准价个数 y</label>
        <input v-model.number="count" type="number" min="1" max="20" />
      </div>
      <div class="form-group">
        <label>网格大小 z</label>
        <input v-model.number="gridSize" type="number" min="0" step="0.1" />
      </div>
    </div>

    <div v-if="result.length > 0" class="result">
      <h3>新的基准价（{{ result.length }} 个）</h3>
      <div class="result-list">
        <span v-for="(price, idx) in result" :key="idx" class="price-tag">
          {{ formatPrice(price) }}
        </span>
      </div>
      <p class="result-info">
        间隔：{{ formatPrice(gridSize / count) }} | 范围：{{ formatPrice(result[0]) }} ~ {{ formatPrice(result[result.length - 1]) }}
      </p>
    </div>
    <div v-else class="placeholder">
      输入有效的网格基准价和参数后，结果将在此显示
    </div>
  </div>
</template>
