<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts'

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

const tabs = [
  { key: 'local', label: '本地K线' },
  { key: 'eastmoney', label: '东方财富' },
  { key: 'xueqiu', label: '雪球' },
]
const activeTab = ref('local')

function selectTab(tab) {
  if (tab.key === 'xueqiu') {
    window.open(xueqiuUrl.value, '_blank', 'noopener')
    return
  }
  activeTab.value = tab.key
}

const marketId = computed(() => {
  return /^(5|6|9|1[13])/.test(props.code) ? '1' : '0'
})

const marketPrefix = computed(() => (marketId.value === '1' ? 'SH' : 'SZ'))

const baseURL = useRuntimeConfig().app.baseURL

let fundamentalCache = null

function parseFundamentals(text) {
  const map = {}
  if (!text) return map
  const lines = text.replace(/^\uFEFF/, '').trim().split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  const codeIdx = headers.indexOf('代码')
  const peIdx = headers.indexOf('PE(TTM)')
  const roeIdx = headers.indexOf('ROE(TTM)')
  const growthIdx = headers.indexOf('净利同比')
  if (codeIdx === -1) return map
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',')
    map[cols[codeIdx]?.trim()] = {
      pe: peIdx === -1 ? '' : cols[peIdx]?.trim(),
      roe: roeIdx === -1 ? '' : cols[roeIdx]?.trim(),
      growth: growthIdx === -1 ? '' : cols[growthIdx]?.trim(),
    }
  }
  return map
}

function loadFundamentals(url) {
  if (!fundamentalCache) {
    fundamentalCache = fetch(`${url}data/stock_fundamental.csv`)
      .then(res => (res.ok ? res.text() : ''))
      .then(parseFundamentals)
      .catch(() => ({}))
  }
  return fundamentalCache
}

const fundamental = ref(null)

function fmtNum(value, digits = 2) {
  const num = parseFloat(value)
  return isNaN(num) ? '-' : num.toFixed(digits)
}

function fmtPct(value, digits = 1) {
  const num = parseFloat(value)
  return isNaN(num) ? '-' : `${num.toFixed(digits)}%`
}

const eastmoneyUrl = computed(
  () => `${baseURL}baidu.com.html?market=${marketId.value}&code=${props.code}`,
)

const xueqiuUrl = computed(() => `https://xueqiu.com/S/${marketPrefix.value}${props.code}`)

const eastmoneyLoading = ref(true)

const chartContainer = ref(null)
const loading = ref(true)
const error = ref('')
const klineData = ref([])
const volumeData = ref([])
let chart = null

async function loadData() {
  loading.value = true
  error.value = ''

  try {
    const res = await fetch(`${baseURL}data/${props.code}_close.csv`)
    if (!res.ok) throw new Error('数据文件不存在')
    const text = await res.text()
    parseData(text)
  } catch (e) {
    error.value = e.message || '加载数据失败'
    loading.value = false
  }
}

function parseData(text) {
  const lines = text.trim().split('\n')
  if (lines.length < 2) {
    error.value = '数据为空'
    loading.value = false
    return
  }

  const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
  const dateIdx = headers.findIndex(h => h.includes('date') || h.includes('日期'))
  const openIdx = headers.findIndex(h => h.includes('open') || h.includes('开盘'))
  const highIdx = headers.findIndex(h => h.includes('high') || h.includes('最高'))
  const lowIdx = headers.findIndex(h => h.includes('low') || h.includes('最低'))
  const closeIdx = headers.findIndex(h => h.includes('close') || h.includes('收盘'))
  const volumeIdx = headers.findIndex(h => h.includes('volume') || h.includes('成交量'))

  if (dateIdx === -1 || openIdx === -1 || highIdx === -1 || lowIdx === -1 || closeIdx === -1) {
    error.value = 'CSV格式不正确，需要包含 date, open, high, low, close 列'
    loading.value = false
    return
  }

  const klines = []
  const volumes = []

  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',')
    if (cols.length < 5) continue

    const dateStr = cols[dateIdx].trim()
    const open = parseFloat(cols[openIdx])
    const high = parseFloat(cols[highIdx])
    const low = parseFloat(cols[lowIdx])
    const close = parseFloat(cols[closeIdx])

    if (isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close)) continue

    const time = formatDate(dateStr)
    if (!time) continue

    klines.push({ time, open, high, low, close })

    if (volumeIdx !== -1) {
      const volume = parseFloat(cols[volumeIdx])
      if (!isNaN(volume)) {
        volumes.push({
          time,
          value: volume,
          color: close >= open ? 'rgba(0, 150, 136, 0.3)' : 'rgba(239, 83, 80, 0.3)',
        })
      }
    }
  }

  if (klines.length === 0) {
    error.value = '没有有效的K线数据'
    loading.value = false
    return
  }

  klines.sort((a, b) => (a.time < b.time ? -1 : 1))
  volumes.sort((a, b) => (a.time < b.time ? -1 : 1))

  klineData.value = klines
  volumeData.value = volumes
  loading.value = false

  nextTick(() => {
    if (activeTab.value === 'local') renderChart()
  })
}

function formatDate(dateStr) {
  let match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (match) return `${match[1]}-${match[2]}-${match[3]}`
  match = dateStr.match(/^(\d{4})\/(\d{2})\/(\d{2})/)
  if (match) return `${match[1]}-${match[2]}-${match[3]}`
  match = dateStr.match(/^(\d{4})(\d{2})(\d{2})/)
  if (match) return `${match[1]}-${match[2]}-${match[3]}`
  return null
}

function destroyChart() {
  if (chart) {
    chart.remove()
    chart = null
  }
}

function renderChart() {
  if (!chartContainer.value || klineData.value.length === 0) return

  destroyChart()

  const container = chartContainer.value
  const chartWidth = container.clientWidth || 800
  const chartHeight = container.clientHeight || Math.max(400, window.innerHeight * 0.5)

  chart = createChart(container, {
    width: chartWidth,
    height: chartHeight,
    layout: {
      background: { type: ColorType.Solid, color: '#ffffff' },
      textColor: '#333',
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' },
    },
    crosshair: {
      mode: 1,
    },
    rightPriceScale: {
      borderColor: '#ddd',
    },
    timeScale: {
      borderColor: '#ddd',
      timeVisible: true,
      secondsVisible: false,
      fixLeftEdge: true,
      offset: 10,
    },
  })

  const candlestickSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#ef5350',
    downColor: '#26a69a',
    borderDownColor: '#26a69a',
    borderUpColor: '#ef5350',
    wickDownColor: '#26a69a',
    wickUpColor: '#ef5350',
  })

  candlestickSeries.setData(klineData.value)

  if (volumeData.value.length > 0) {
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    volumeSeries.setData(volumeData.value)
  }

  chart.timeScale().fitContent()
  chart.applyOptions({ watermark: { visible: false } })
}

function handleResize() {
  if (activeTab.value === 'local' && chart && chartContainer.value) {
    chart.applyOptions({ width: chartContainer.value.clientWidth })
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

watch(activeTab, (tab) => {
  if (tab === 'local') {
    nextTick(() => renderChart())
  } else {
    destroyChart()
  }
})

onMounted(() => {
  loadData()
  loadFundamentals(baseURL).then(map => {
    fundamental.value = map[props.code] || null
  })
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', handleResize)
  destroyChart()
})
</script>

<template>
  <div class="kline-overlay" @click.self="emit('close')">
    <div class="kline-modal">
      <div class="kline-header">
        <div class="kline-title">
          <h2>{{ name }} ({{ code }})</h2>
          <div v-if="fundamental" class="kline-metrics">
            <span>PE(TTM) <b>{{ fmtNum(fundamental.pe) }}</b></span>
            <span>ROE(TTM) <b>{{ fmtPct(fundamental.roe) }}</b></span>
            <span>净利增速 <b>{{ fmtPct(fundamental.growth) }}</b></span>
          </div>
        </div>
        <button class="kline-close" @click="emit('close')">✕</button>
      </div>
      <div class="kline-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="kline-tab"
          :class="{ active: activeTab === tab.key }"
          @click="selectTab(tab)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="kline-body">
        <template v-if="activeTab === 'local'">
          <div v-if="loading" class="kline-loading">加载中...</div>
          <div v-else-if="error" class="kline-error">{{ error }}</div>
          <div v-else ref="chartContainer" class="kline-chart"></div>
        </template>
        <template v-else-if="activeTab === 'eastmoney'">
          <a :href="eastmoneyUrl" target="_blank" rel="noopener" class="kline-open-link">
            新窗口打开
          </a>
          <div v-if="eastmoneyLoading" class="kline-loading">加载中...</div>
          <iframe
            :src="eastmoneyUrl"
            class="kline-frame"
            frameborder="0"
            sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"
            referrerpolicy="no-referrer"
            @load="eastmoneyLoading = false"
          ></iframe>
        </template>
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
  width: min(1000px, 92vw);
  height: min(844px, 90vh);
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

.kline-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kline-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  color: var(--text);
}

.kline-metrics b {
  color: var(--text-h);
  font-weight: 600;
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

.kline-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 16px 0;
  border-bottom: 1px solid var(--border);
}

.kline-tab {
  border: none;
  background: none;
  cursor: pointer;
  padding: 8px 14px;
  font-size: 14px;
  color: var(--text);
  opacity: 0.6;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.kline-tab:hover {
  opacity: 1;
}

.kline-tab.active {
  opacity: 1;
  color: var(--text-h);
  font-weight: 600;
  border-bottom-color: #e74c3c;
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
  z-index: 3;
}

.kline-chart {
  width: 100%;
  height: 100%;
  padding: 12px;
  box-sizing: border-box;
}

.kline-chart :deep([class*="watermark"]) {
  display: none !important;
}

.kline-chart :deep(a[href*="tradingview"]) {
  display: none !important;
}

.kline-chart :deep(svg[class*="watermark"]) {
  display: none !important;
}

.kline-frame {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 390px;
  max-width: 100%;
  height: calc(100% + 120px);
  border: none;
  display: block;
}

.kline-open-link {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 4;
  padding: 4px 10px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 12px;
  text-decoration: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.kline-open-link:hover {
  color: #e74c3c;
}

@media (prefers-color-scheme: dark) {
  .kline-modal {
    background: #1a1b26;
  }
}
</style>
