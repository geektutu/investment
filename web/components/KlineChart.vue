<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
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
  csvPath: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])

const chartContainer = ref(null)
const loading = ref(true)
const error = ref('')
let chart = null

const config = useRuntimeConfig()
const baseUrl = config.app.baseURL || '/'

async function loadData() {
  loading.value = true
  error.value = ''

  try {
    const csvFile = props.csvPath || `${props.code}_close.csv`
    const res = await fetch(`${baseUrl}data/${csvFile}`)
    if (!res.ok) throw new Error('数据文件不存在')
    const text = await res.text()
    parseAndRender(text)
  } catch (e) {
    error.value = e.message || '加载数据失败'
    loading.value = false
  }
}

function parseAndRender(text) {
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

  const klineData = []
  const volumeData = []

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

    klineData.push({
      time,
      open,
      high,
      low,
      close,
    })

    if (volumeIdx !== -1) {
      const volume = parseFloat(cols[volumeIdx])
      if (!isNaN(volume)) {
        volumeData.push({
          time,
          value: volume,
          color: close >= open ? 'rgba(0, 150, 136, 0.3)' : 'rgba(239, 83, 80, 0.3)',
        })
      }
    }
  }

  if (klineData.length === 0) {
    error.value = '没有有效的K线数据'
    loading.value = false
    return
  }

  // 按时间排序
  klineData.sort((a, b) => a.time - b.time)
  volumeData.sort((a, b) => a.time - b.time)

  // 关闭 loading，等待 Vue 渲染容器后再渲染图表
  loading.value = false
  nextTick(() => {
    nextTick(() => {
      renderChart(klineData, volumeData)
    })
  })
}

function formatDate(dateStr) {
  // 支持格式：YYYY-MM-DD 或 YYYY/MM/DD 或 YYYYMMDD
  let match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]}`
  }
  match = dateStr.match(/^(\d{4})\/(\d{2})\/(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]}`
  }
  match = dateStr.match(/^(\d{4})(\d{2})(\d{2})/)
  if (match) {
    return `${match[1]}-${match[2]}-${match[3]}`
  }
  return null
}

function renderChart(klineData, volumeData) {
  if (!chartContainer.value) return

  // 清除旧图表
  if (chart) {
    chart.remove()
    chart = null
  }

  const container = chartContainer.value
  const chartWidth = container.clientWidth || 800
  const chartHeight = Math.max(400, window.innerHeight * 0.5)

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

  // v5 API: 使用 addSeries 并传入系列类型
  const candlestickSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#ef5350',
    downColor: '#26a69a',
    borderDownColor: '#26a69a',
    borderUpColor: '#ef5350',
    wickDownColor: '#26a69a',
    wickUpColor: '#ef5350',
  })

  candlestickSeries.setData(klineData)

  if (volumeData.length > 0) {
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

    volumeSeries.setData(volumeData)
  }

  chart.timeScale().fitContent()

  // 移除水印
  chart.applyOptions({
    watermark: {
      visible: false,
    },
  })
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  loadData()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (chart) {
    chart.remove()
    chart = null
  }
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
        <div v-else-if="error" class="kline-error">{{ error }}</div>
        <div v-else ref="chartContainer" class="kline-chart"></div>
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
  max-height: 80vh;
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
  overflow: auto;
  padding: 16px;
}

.kline-loading,
.kline-error {
  text-align: center;
  padding: 60px 0;
  color: var(--text);
}

.kline-error {
  color: #e74c3c;
}

.kline-chart {
  width: 100%;
  min-height: 400px;
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

.kline-chart :deep(div[style*="position: absolute"][style*="bottom"]) {
  display: none !important;
}

@media (prefers-color-scheme: dark) {
  .kline-modal {
    background: #1a1b26;
  }
}
</style>
