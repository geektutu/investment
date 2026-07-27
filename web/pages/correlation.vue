<script setup>
import CorrelationHeatmap from '~/components/CorrelationHeatmap.vue'
</script>

<template>
  <div class="container">
    <h1>ETF 相关性热力图</h1>
    <p class="description">展示 ETF 之间的涨跌幅相关性，数值范围 -1（完全负相关）到 +1（完全正相关）</p>
    <CorrelationHeatmap csvPath="correlation.csv" />
  </div>
</template>

<style scoped>
.description {
  text-align: center;
  color: var(--text);
  margin-bottom: 24px;
  font-size: 14px;
}
</style>
