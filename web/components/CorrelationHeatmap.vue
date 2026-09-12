<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  csvPath: {
    type: String,
    default: 'correlation.csv',
  },
})

const codes = ref([])
const names = ref({})
const matrix = ref([])

const config = useRuntimeConfig()
const baseUrl = config.app.baseURL || '/'

onMounted(async () => {
  const res = await fetch(`${baseUrl}data/${props.csvPath}`)
  const text = await res.text()
  parseCSV(text)
})

function parseCSV(text) {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return

  // 第一行是表头，提取代码列表
  const headers = lines[0].split(',')
  codes.value = headers.slice(2) // 跳过"代码"和"名称"

  // 解析每行数据
  const data = []
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',')
    const code = cols[0]
    const name = cols[1]
    names.value[code] = name
    const row = cols.slice(2).map(v => parseFloat(v) || 0)
    data.push(row)
  }
  matrix.value = data
}

// 根据相关性值返回颜色
function getColor(value) {
  if (value >= 0) {
    const intensity = Math.min(value, 1)
    const r = 255
    const g = Math.round(255 * (1 - intensity * 0.8))
    const b = Math.round(255 * (1 - intensity * 0.8))
    return `rgb(${r}, ${g}, ${b})`
  } else {
    const intensity = Math.min(Math.abs(value), 1)
    const r = Math.round(255 * (1 - intensity * 0.8))
    const g = Math.round(255 * (1 - intensity * 0.8))
    const b = 255
    return `rgb(${r}, ${g}, ${b})`
  }
}

function getTextColor(value) {
  return Math.abs(value) > 0.5 ? '#fff' : 'var(--text-h)'
}

// 全部强负相关组合（< -0.5），按相关性升序（矩阵对称故只遍历上三角）
const negativePairs = computed(() => {
  const result = []
  const n = codes.value.length
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const value = matrix.value[i]?.[j] ?? 0
      if (value < -0.5) {
        result.push({ i, j, value })
      }
    }
  }
  return result.sort((a, b) => a.value - b.value)
})

// 按 ETF 聚合：每对只归到强负相关对数更多的一侧，避免同一对出现两次
const negativeGroups = computed(() => {
  const countByCode = new Map()
  for (const { i, j } of negativePairs.value) {
    const a = codes.value[i]
    const b = codes.value[j]
    countByCode.set(a, (countByCode.get(a) || 0) + 1)
    countByCode.set(b, (countByCode.get(b) || 0) + 1)
  }
  const groups = new Map()
  for (const { i, j, value } of negativePairs.value) {
    const a = codes.value[i]
    const b = codes.value[j]
    const anchor = (countByCode.get(a) || 0) >= (countByCode.get(b) || 0) ? a : b
    const partner = anchor === a ? b : a
    if (!groups.has(anchor)) {
      groups.set(anchor, { code: anchor, name: names.value[anchor], partners: [] })
    }
    groups.get(anchor).partners.push({
      code: partner,
      name: names.value[partner],
      value,
    })
  }
  const list = Array.from(groups.values())
  for (const group of list) {
    group.partners.sort((a, b) => a.value - b.value)
  }
  return list.sort((a, b) => b.partners.length - a.partners.length)
})

const cellSize = computed(() => {
  const n = codes.value.length
  if (n <= 10) return 60
  if (n <= 20) return 45
  return 35
})
</script>

<template>
  <div class="correlation-heatmap">
    <div v-if="negativeGroups.length" class="top-negative">
      <div class="top-negative-title">强负相关 &lt; -0.5（共 {{ negativePairs.length }} 对）</div>
      <div v-for="group in negativeGroups" :key="group.code" class="neg-group">
        <div class="neg-group-anchor">
          {{ group.name }}
          <span class="count">({{ group.partners.length }})</span>
        </div>
        <div class="neg-group-partners">
          <span v-for="p in group.partners" :key="p.code" class="partner">
            {{ p.name }}<span class="value">{{ p.value.toFixed(2) }}</span>
          </span>
        </div>
      </div>
    </div>
    <div class="heatmap-scroll">
      <table class="heatmap-table">
        <thead>
          <tr>
            <th class="corner-cell">
              <div class="header-text">代码</div>
            </th>
            <th v-for="code in codes" :key="code" class="col-header">
              <div class="header-text">
                <span class="code">{{ code }}</span>
                <span class="name">{{ names[code] }}</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in matrix" :key="codes[i]">
            <td class="row-header">
              <span class="code">{{ codes[i] }}</span>
              <span class="name">{{ names[codes[i]] }}</span>
            </td>
            <td
              v-for="(val, j) in row"
              :key="j"
              class="heatmap-cell"
              :style="{
                backgroundColor: getColor(val),
                color: getTextColor(val),
                width: cellSize + 'px',
                height: cellSize + 'px',
              }"
              :title="`${names[codes[i]]} vs ${names[codes[j]]}: ${val.toFixed(4)}`"
            >
              {{ val.toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="legend">
      <span class="legend-label">-1</span>
      <div class="legend-gradient"></div>
      <span class="legend-label">+1</span>
    </div>
  </div>
</template>

<style scoped>
.correlation-heatmap {
  overflow-x: auto;
}

.heatmap-scroll {
  overflow-x: auto;
  max-height: 70vh;
  overflow-y: auto;
}

.heatmap-table {
  border-collapse: separate;
  border-spacing: 0;
  font-size: 11px;
  width: auto;
  overflow: visible;
  box-shadow: none;
  border-radius: 0;
}

.corner-cell {
  position: sticky;
  top: 0;
  left: 0;
  background: var(--bg);
  z-index: 5;
  width: 100px;
  min-width: 100px;
  padding: 4px 8px;
  border: 1px solid var(--border);
  text-align: center;
}

.col-header {
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 2;
  padding: 4px;
  border: 1px solid var(--border);
}

.header-text {
  font-weight: 600;
  color: var(--text-h);
}

.col-header .header-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  min-width: 60px;
  max-width: 100px;
  white-space: normal;
  word-break: break-all;
  text-align: center;
}

.col-header .code {
  font-family: var(--mono);
  font-size: 11px;
  line-height: 1.2;
}

.col-header .name {
  font-size: 10px;
  font-weight: 400;
  opacity: 0.8;
  overflow-wrap: break-word;
  line-height: 1.2;
  text-align: center;
}

.row-header {
  position: sticky;
  left: 0;
  background: var(--bg);
  z-index: 1;
  width: 100px;
  min-width: 100px;
  padding: 4px 8px;
  border: 1px solid var(--border);
  white-space: nowrap;
}

.row-header .code {
  font-family: var(--mono);
  font-weight: 600;
  color: var(--accent);
  margin-right: 8px;
}

.row-header .name {
  color: var(--text);
  font-size: 12px;
}

.heatmap-cell {
  text-align: center;
  cursor: pointer;
  transition: transform 0.1s;
  border: 1px solid var(--border);
  font-family: var(--mono);
}

.heatmap-cell:hover {
  transform: scale(1.1);
  z-index: 10;
  position: relative;
  box-shadow: var(--shadow);
}

.top-negative {
  margin-bottom: 16px;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  max-width: 720px;
}

.top-negative-title {
  font-weight: 600;
  color: var(--text-h);
  margin-bottom: 8px;
}

.neg-group {
  padding: 6px 0;
  border-top: 1px solid var(--border);
}

.top-negative-title + .neg-group {
  border-top: none;
}

.neg-group-anchor {
  font-weight: 600;
  color: var(--text-h);
  margin-bottom: 4px;
}

.neg-group-anchor .count {
  font-weight: 400;
  font-size: 12px;
  opacity: 0.7;
  margin-left: 2px;
}

.neg-group-partners {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  font-size: 12px;
}

.neg-group-partners .partner {
  color: var(--text);
  white-space: nowrap;
}

.neg-group-partners .value {
  font-family: var(--mono);
  color: #2563eb;
  margin-left: 2px;
}

.legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 12px;
  color: var(--text);
}

.legend-gradient {
  width: 200px;
  height: 12px;
  background: linear-gradient(to right, rgb(153, 153, 255), white, rgb(255, 153, 153));
  border-radius: 6px;
  border: 1px solid var(--border);
}
</style>
