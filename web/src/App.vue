<script setup>
import { ref, onMounted } from 'vue'

const headers = ref([])
const rows = ref([])
const buildTime = ref(new Date(__BUILD_TIME__).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }))

onMounted(async () => {
  const baseUrl = import.meta.env.VITE_BASE_URL || '/'
  const res = await fetch(`${baseUrl}data/etf_atr.csv`)
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
      atr: cols[2]?.trim(),
      maxDrawdown: cols[3]?.trim(),
      currentDrawdown: cols[4]?.trim(),
    }
  })
}
</script>

<template>
  <header class="header">
    <div class="site-brand">
      <img src="/rabbit.png" alt="logo" class="logo" />
      <span class="site-name">投资小兔兔</span>
    </div>
    <a href="https://github.com/geektutu/investment" target="_blank" class="github-link">GitHub</a>
  </header>
  <div class="container">
    <h1>ETF ATR 数据表</h1>
    <table>
      <thead>
        <tr>
          <th v-for="h in headers" :key="h">{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.code">
          <td><code>{{ row.code }}</code></td>
          <td>{{ row.name }}</td>
          <td>{{ row.atr }}</td>
          <td>{{ row.maxDrawdown }}</td>
          <td>{{ row.currentDrawdown }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <footer class="footer">
    构建时间：{{ buildTime }}
  </footer>
</template>
