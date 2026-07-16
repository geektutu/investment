<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  csvPath: {
    type: String,
    required: true,
  },
})

const headers = ref([])
const rows = ref([])
const sortKey = ref('')
const sortAsc = ref(true)
const selectedSources = ref([])
const showSourceFilter = ref(false)

const sortableIndexes = [2, 3, 4, 5]

const config = useRuntimeConfig()
const baseUrl = config.app.baseURL || '/'

onMounted(async () => {
  const res = await fetch(`${baseUrl}data/${props.csvPath}`)
  const text = await res.text()
  parseCSV(text)
})

function parseCSV(text) {
  const lines = text.trim().split('\n')
  headers.value = lines[0].split(',').map(h => h.trim())
  rows.value = lines.slice(1).map(line => {
    const cols = line.split(',')
    return {
      code: cols[0]?.trim(),
      name: cols[1]?.trim(),
      atr14: cols[2]?.trim(),
      atr60: cols[3]?.trim(),
      maxDrawdown: cols[4]?.trim(),
      currentDrawdown: cols[5]?.trim(),
      source: cols[6]?.trim(),
    }
  })
}

function parsePercent(val) {
  return parseFloat(val?.replace('%', '')) || 0
}

const allSources = computed(() => {
  const sources = new Set()
  rows.value.forEach(row => {
    if (row.source) sources.add(row.source)
  })
  return Array.from(sources).sort()
})

const filteredRows = computed(() => {
  if (selectedSources.value.length === 0) return rows.value
  return rows.value.filter(row => selectedSources.value.includes(row.source))
})

const sortedRows = computed(() => {
  const data = filteredRows.value
  if (!sortKey.value) return data
  const idx = parseInt(sortKey.value)
  const sorted = [...data].sort((a, b) => {
    const keyMap = { 2: 'atr14', 3: 'atr60', 4: 'maxDrawdown', 5: 'currentDrawdown' }
    const field = keyMap[idx]
    return parsePercent(a[field]) - parsePercent(b[field])
  })
  return sortAsc.value ? sorted : sorted.reverse()
})

function toggleSort(idx) {
  if (sortKey.value === idx.toString()) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = idx.toString()
    sortAsc.value = true
  }
}

function sortIcon(idx) {
  if (sortKey.value !== idx.toString()) return ' ↕'
  return sortAsc.value ? ' ↑' : ' ↓'
}

function toggleSource(source) {
  const idx = selectedSources.value.indexOf(source)
  if (idx === -1) {
    selectedSources.value.push(source)
  } else {
    selectedSources.value.splice(idx, 1)
  }
}

function clearSources() {
  selectedSources.value = []
}

function selectAllSources() {
  selectedSources.value = [...allSources.value]
}

function toggleFilterPanel() {
  showSourceFilter.value = !showSourceFilter.value
}

function closePanel() {
  showSourceFilter.value = false
}
</script>

<template>
  <div class="atr-table-wrapper">
    <table>
      <thead>
        <tr>
          <th v-for="(h, idx) in headers" :key="h" :class="{ 'atr-sortable': sortableIndexes.includes(idx) }" @click="sortableIndexes.includes(idx) && toggleSort(idx)">
            <template v-if="h === '来源'">
              <div class="source-filter-wrapper">
                <span class="source-header" @click.stop="toggleFilterPanel">
                  {{ h }}<span class="filter-arrow">{{ showSourceFilter ? ' ▼' : ' ▾' }}</span>
                </span>
                <div
                  v-if="showSourceFilter"
                  class="source-filter-panel"
                  @click.stop
                >
                  <div class="filter-header">
                    <span>筛选来源</span>
                    <button class="filter-btn" @click="selectAllSources">全选</button>
                    <button class="filter-btn" @click="clearSources">清空</button>
                    <button class="filter-close" @click="closePanel">✕</button>
                  </div>
                  <div class="filter-options">
                    <label v-for="source in allSources" :key="source" class="filter-option">
                      <input
                        type="checkbox"
                        :checked="selectedSources.includes(source)"
                        @change="toggleSource(source)"
                      />
                      <span>{{ source }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              {{ h }}<span class="atr-sort-icon">{{ sortableIndexes.includes(idx) ? sortIcon(idx) : '' }}</span>
            </template>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in sortedRows" :key="row.code + row.source">
          <td><code>{{ row.code }}</code></td>
          <td>{{ row.name }}</td>
          <td>{{ row.atr14 }}</td>
          <td>{{ row.atr60 }}</td>
          <td>{{ row.maxDrawdown }}</td>
          <td>{{ row.currentDrawdown }}</td>
          <td>{{ row.source }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.atr-table-wrapper {
  overflow: visible;
  position: relative;
  z-index: 1;
}

.atr-table-wrapper table {
  overflow: visible;
}

.atr-sortable {
  cursor: pointer;
  user-select: none;
}

.atr-sortable:hover {
  background: var(--accent-bg);
  color: var(--accent);
}

.atr-sort-icon {
  font-size: 12px;
  opacity: 0.4;
  margin-left: 2px;
}

.atr-sortable:hover .atr-sort-icon,
.atr-sortable:active .atr-sort-icon {
  opacity: 1;
}

.source-filter-wrapper {
  position: relative;
  display: inline-block;
}

.source-header {
  cursor: pointer;
  user-select: none;
}

.filter-arrow {
  font-size: 0.75em;
  margin-left: 4px;
  color: var(--accent);
}

.source-filter-panel {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  box-shadow: var(--shadow);
  padding: 12px;
  z-index: 1000;
  min-width: 180px;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
  color: var(--text-h);
}

.filter-btn {
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
}

.filter-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.filter-close {
  margin-left: auto;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
  opacity: 0.5;
}

.filter-close:hover {
  opacity: 1;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
}

.filter-option:hover {
  color: var(--accent);
}
</style>
