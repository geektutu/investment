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

const cellSize = computed(() => {
  const n = codes.value.length
  if (n <= 10) return 60
  if (n <= 20) return 45
  return 35
})
</script>

<template>
  <div class="correlation-heatmap">
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
