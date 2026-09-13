<script setup>
const route = useRoute()
const baseURL = useRuntimeConfig().app.baseURL
const { buildTime } = useAppConfig()
const openGroup = ref('')

const navGroups = [
  {
    label: '数据',
    to: '/atr',
    match: ['/', '/atr', '/stock-atr', '/correlation'],
    children: [
      { label: 'ETF ATR', to: '/atr' },
      { label: '个股 ATR', to: '/stock-atr' },
      { label: '相关性', to: '/correlation' },
    ],
  },
  {
    label: '工具',
    to: '/tools/todo',
    match: ['/tools'],
    children: [
      { label: '网格', to: '/tools/grid' },
      { label: 'ToDo', to: '/tools/todo' },
    ],
  },
]

function isActive(group) {
  return group.match.some(p => (p === '/' ? route.path === '/' : route.path.startsWith(p)))
}

function toggleGroup(label) {
  if (typeof window !== 'undefined' && window.matchMedia('(hover: hover)').matches) return
  openGroup.value = openGroup.value === label ? '' : label
}

function closeGroup() {
  openGroup.value = ''
}

watch(() => route.fullPath, closeGroup)
</script>

<template>
  <div>
    <header class="header">
      <div class="site-brand">
        <img :src="`${baseURL}rabbit.png`" alt="logo" class="logo" />
        <span class="site-name">投资小兔兔</span>
      </div>
      <nav class="tabs">
        <div
          v-for="group in navGroups"
          :key="group.label"
          class="tab-item"
          :class="{ active: isActive(group), open: openGroup === group.label }"
        >
          <button
            v-if="group.children.length"
            class="tab-link"
            @click="toggleGroup(group.label)"
          >
            {{ group.label }}<span class="tab-caret">▾</span>
          </button>
          <NuxtLink v-else :to="group.to" class="tab-link">{{ group.label }}</NuxtLink>
          <div v-if="group.children.length" class="tab-dropdown">
            <NuxtLink
              v-for="child in group.children"
              :key="child.to"
              :to="child.to"
              class="tab-dropdown-link"
              :class="{ active: route.path === child.to }"
              @click="closeGroup"
            >
              {{ child.label }}
            </NuxtLink>
          </div>
        </div>
      </nav>
      <a href="https://github.com/geektutu/investment" target="_blank" class="github-link">GitHub</a>
    </header>
    <slot />
    <footer class="footer">
      构建时间：{{ buildTime }}
    </footer>
  </div>
</template>
