<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  { path: '/atr', name: 'ETF ATR' },
]
</script>

<template>
  <div class="container">
    <h1>投资数据</h1>
    <div class="grid-layout">
      <aside class="sidebar">
        <ul class="menu">
          <li v-for="item in menuItems" :key="item.path">
            <router-link :to="item.path" :class="{ active: route.path === item.path }">
              {{ item.name }}
            </router-link>
          </li>
        </ul>
      </aside>
      <main class="content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>
