<script setup>
import CorrelationHeatmap from '~/components/CorrelationHeatmap.vue'
</script>

<template>
  <div>
    <h2>ETF 相关性热力图</h2>
    <p class="description">展示 ETF 之间的涨跌幅相关性，数值范围 -1（完全负相关）到 +1（完全正相关）</p>
    <CorrelationHeatmap csvPath="correlation.csv" />
  </div>
</template>

<style scoped>
h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.description {
  color: var(--text);
  margin-bottom: 20px;
  font-size: 13px;
  opacity: 0.7;
}
</style>
