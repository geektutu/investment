<script setup>
import { ref, onMounted, watch, computed } from 'vue'

const todos = ref([])
const categories = ref(['默认'])
const newTodo = ref('')
const selectedCategory = ref('默认')
const newCategory = ref('')
const showAddCategory = ref(false)
const collapsedCategories = ref([])

onMounted(() => {
  const saved = localStorage.getItem('grid-todos')
  if (saved) todos.value = JSON.parse(saved)
  const savedCategories = localStorage.getItem('grid-categories')
  if (savedCategories) categories.value = JSON.parse(savedCategories)
  const savedCollapsed = localStorage.getItem('grid-collapsed')
  if (savedCollapsed) collapsedCategories.value = JSON.parse(savedCollapsed)
})

watch(todos, (val) => {
  localStorage.setItem('grid-todos', JSON.stringify(val))
}, { deep: true })

watch(categories, (val) => {
  localStorage.setItem('grid-categories', JSON.stringify(val))
}, { deep: true })

watch(collapsedCategories, (val) => {
  localStorage.setItem('grid-collapsed', JSON.stringify(val))
}, { deep: true })

const groupedTodos = computed(() => {
  const groups = {}
  categories.value.forEach(cat => {
    groups[cat] = todos.value.filter(t => t.category === cat)
  })
  return groups
})

function addCategory() {
  const name = newCategory.value.trim()
  if (!name || categories.value.includes(name)) return
  categories.value.push(name)
  newCategory.value = ''
  showAddCategory.value = false
}

function removeCategory(name) {
  if (name === '默认') return
  categories.value = categories.value.filter(c => c !== name)
  todos.value.forEach(t => {
    if (t.category === name) t.category = '默认'
  })
  if (selectedCategory.value === name) selectedCategory.value = '默认'
}

function addTodo() {
  const text = newTodo.value.trim()
  if (!text) return
  todos.value.push({
    id: Date.now(),
    text,
    done: false,
    category: selectedCategory.value,
    createdAt: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
  })
  newTodo.value = ''
}

function toggleTodo(id) {
  const todo = todos.value.find(t => t.id === id)
  if (todo) todo.done = !todo.done
}

function removeTodo(id) {
  todos.value = todos.value.filter(t => t.id !== id)
}

function clearDone() {
  todos.value = todos.value.filter(t => !t.done)
}

function toggleCollapse(category) {
  const idx = collapsedCategories.value.indexOf(category)
  if (idx === -1) {
    collapsedCategories.value.push(category)
  } else {
    collapsedCategories.value.splice(idx, 1)
  }
}

function isCollapsed(category) {
  return collapsedCategories.value.includes(category)
}

const totalCount = computed(() => todos.value.length)
const doneCount = computed(() => todos.value.filter(t => t.done).length)
</script>

<template>
  <div class="todo-container">
    <div class="todo-input-row">
      <input
        v-model="newTodo"
        type="text"
        placeholder="添加新任务..."
        class="todo-input"
        @keyup.enter="addTodo"
      />
      <button class="todo-add-btn" @click="addTodo">添加</button>
    </div>

    <div class="category-row">
      <div class="category-tags">
        <span
          v-for="cat in categories"
          :key="cat"
          class="category-tag"
          :class="{ active: selectedCategory === cat }"
          @click="selectedCategory = cat"
        >
          {{ cat }}
          <button
            v-if="cat !== '默认'"
            class="category-remove"
            @click.stop="removeCategory(cat)"
          >✕</button>
        </span>
      </div>
      <div class="category-actions">
        <button v-if="!showAddCategory" class="category-add-btn" @click="showAddCategory = true">+ 类别</button>
        <div v-else class="category-add-row">
          <input
            v-model="newCategory"
            type="text"
            placeholder="类别名称"
            class="category-add-input"
            @keyup.enter="addCategory"
          />
          <button class="category-confirm-btn" @click="addCategory">确认</button>
          <button class="category-cancel-btn" @click="showAddCategory = false; newCategory = ''">取消</button>
        </div>
      </div>
    </div>

    <div class="todo-stats">
      <span>共 {{ totalCount }} 项</span>
      <span>已完成 {{ doneCount }} 项</span>
      <button v-if="doneCount > 0" class="todo-clear-btn" @click="clearDone">
        清除已完成
      </button>
    </div>

    <div v-for="cat in categories" :key="cat" class="todo-category-section">
      <div
        v-if="groupedTodos[cat] && groupedTodos[cat].length > 0"
        class="category-header"
        @click="toggleCollapse(cat)"
      >
        <span class="category-toggle">{{ isCollapsed(cat) ? '▶' : '▼' }}</span>
        <span class="category-name">{{ cat }}</span>
        <span class="category-count">{{ groupedTodos[cat].length }}</span>
      </div>
      <ul v-show="!isCollapsed(cat)" class="todo-list">
        <li
          v-for="todo in groupedTodos[cat]"
          :key="todo.id"
          class="todo-item"
          :class="{ done: todo.done }"
        >
          <input
            type="checkbox"
            :checked="todo.done"
            @change="toggleTodo(todo.id)"
            class="todo-checkbox"
          />
          <span class="todo-text">{{ todo.text }}</span>
          <span class="todo-date">{{ todo.createdAt }}</span>
          <button class="todo-remove-btn" @click="removeTodo(todo.id)">✕</button>
        </li>
      </ul>
    </div>

    <p v-if="totalCount === 0" class="todo-empty">暂无任务</p>
  </div>
</template>

<style scoped>
.todo-container {
  max-width: 600px;
}

.todo-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.todo-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
}

.todo-input:focus {
  outline: none;
  border-color: var(--accent);
}

.todo-add-btn {
  padding: 8px 16px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.todo-add-btn:hover {
  opacity: 0.85;
}

.category-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.category-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.category-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  background: var(--bg);
  color: var(--text);
  transition: all 0.2s;
}

.category-tag:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.category-tag.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.category-remove {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  opacity: 0.5;
  padding: 0;
  color: inherit;
}

.category-remove:hover {
  opacity: 1;
}

.category-actions {
  margin-left: auto;
}

.category-add-btn {
  padding: 4px 10px;
  font-size: 13px;
  border: 1px dashed var(--border);
  border-radius: 16px;
  background: none;
  color: var(--text);
  cursor: pointer;
  opacity: 0.7;
}

.category-add-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  opacity: 1;
}

.category-add-row {
  display: flex;
  gap: 4px;
  align-items: center;
}

.category-add-input {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 13px;
  background: var(--bg);
  color: var(--text);
  width: 100px;
}

.category-add-input:focus {
  outline: none;
  border-color: var(--accent);
}

.category-confirm-btn,
.category-cancel-btn {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
}

.category-confirm-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.category-cancel-btn:hover {
  border-color: #e74c3c;
  color: #e74c3c;
}

.todo-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--text);
  opacity: 0.7;
}

.todo-clear-btn {
  margin-left: auto;
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
}

.todo-clear-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.todo-category-section {
  margin-bottom: 12px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.category-header:hover {
  color: var(--accent);
}

.category-toggle {
  font-size: 12px;
  opacity: 0.6;
}

.category-name {
  font-weight: 600;
  font-size: 14px;
}

.category-count {
  font-size: 12px;
  opacity: 0.5;
  margin-left: auto;
}

.todo-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 8px;
  background: var(--bg);
}

.todo-item.done .todo-text {
  text-decoration: line-through;
  opacity: 0.5;
}

.todo-checkbox {
  cursor: pointer;
}

.todo-text {
  flex: 1;
  font-size: 14px;
}

.todo-date {
  font-size: 12px;
  opacity: 0.5;
}

.todo-remove-btn {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
  opacity: 0.4;
}

.todo-remove-btn:hover {
  opacity: 1;
  color: #e74c3c;
}

.todo-empty {
  text-align: center;
  padding: 40px 0;
  opacity: 0.5;
}
</style>
