<script setup>
import { ref, computed } from 'vue'

const basePrices = ref('30')
const count = ref(1)
const gridSize = ref(2)
const positionQuantity = ref(1000)
const quantityPerTrade = ref(100)

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

const gridRatio = computed(() => {
  if (average.value === 0) return 0
  return gridSize.value / average.value
})

const supportIncrease = computed(() => {
  if (count.value === 0 || quantityPerTrade.value === 0 || average.value === 0) return 0
  return positionQuantity.value / quantityPerTrade.value / count.value * gridRatio.value
})

const riskOnePercent = computed(() => {
  if (gridRatio.value === 0) return 0
  return quantityPerTrade.value * average.value * count.value / gridRatio.value / 100
})

const amountPerTrade = computed(() => {
  return average.value * quantityPerTrade.value
})

const targetPrice = computed(() => {
  if (count.value === 0 || quantityPerTrade.value === 0) return 0
  return average.value + positionQuantity.value / quantityPerTrade.value / count.value * gridSize.value
})

function formatPrice(val) {
  return val.toFixed(3)
}

function formatPercent(val) {
  return (val * 100).toFixed(2) + '%'
}
</script>

<template>
  <div class="calculator">
    <div class="form-row">
      <div class="form-group">
        <label>网格基准价</label>
        <input v-model="basePrices" type="text" placeholder="如：100,110,105" />
      </div>
      <div class="form-group">
        <label>基准价个数</label>
        <input v-model.number="count" type="number" min="1" max="20" class="input-narrow" />
      </div>
      <div class="form-group">
        <label>网格大小</label>
        <input v-model.number="gridSize" type="number" min="0" step="0.1" class="input-narrow" />
      </div>
      <div class="form-group">
        <label>持仓数量</label>
        <input v-model.number="positionQuantity" type="number" min="0" class="input-narrow" />
      </div>
      <div class="form-group">
        <label>每笔数量</label>
        <input v-model.number="quantityPerTrade" type="number" min="0" class="input-narrow" />
      </div>
    </div>

    <div v-if="result.length > 0" class="result">
      <div class="result-row">
        <div class="result-left">
          <label class="result-label">新的基准价（{{ result.length }} 个）</label>
          <div class="result-list">
            <span v-for="(price, idx) in result" :key="idx" class="price-tag">
              {{ formatPrice(price) }}
            </span>
          </div>
        </div>
        <div class="result-metrics">
          <div class="metric-item">
            <span class="metric-label">网格比例</span>
            <span class="metric-value">{{ formatPercent(gridRatio) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">支撑涨幅</span>
            <span class="metric-value">{{ formatPercent(supportIncrease) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">每笔金额</span>
            <span class="metric-value">{{ Math.round(amountPerTrade) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">1%风险</span>
            <span class="metric-value">{{ Math.round(riskOnePercent) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">目标价格</span>
            <span class="metric-value">{{ formatPrice(targetPrice) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="placeholder">
      输入有效的网格基准价和参数后，结果将在此显示
    </div>
  </div>
</template>

<style scoped>
.form-group label {
  white-space: nowrap;
}

.input-narrow {
  width: 80px;
}

.result-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-h);
  display: block;
  margin-bottom: 10px;
}

.price-tag {
  font-size: 15px;
}

.result-row {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.result-left {
  flex: 1;
  min-width: 0;
}

.result-metrics {
  display: flex;
  gap: 16px;
  flex-shrink: 0;
  padding-top: 30px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.metric-label {
  font-size: 11px;
  opacity: 0.7;
  white-space: nowrap;
}

.metric-value {
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
</style>
