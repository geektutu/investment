<template>
  <div class="container">
    <h1>工具</h1>
    <div class="grid-layout">
      <aside class="sidebar">
        <ul class="menu">
          <li>
            <NuxtLink to="/tools/todo" :class="{ 'active': $route.path === '/tools/todo' }">
              ToDo
            </NuxtLink>
          </li>
        </ul>
      </aside>
      <main class="content">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>
