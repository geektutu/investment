<script setup>
import Calculator from '~/components/Calculator.vue'
</script>

<template>
  <div class="container">
    <h1>网格交易</h1>
    <div class="grid-layout">
      <aside class="sidebar">
        <ul class="menu">
          <li>
            <NuxtLink to="/grid" class="active">
              网格计算器
            </NuxtLink>
          </li>
        </ul>
      </aside>
      <main class="content">
        <Calculator />
      </main>
    </div>
  </div>
</template>
