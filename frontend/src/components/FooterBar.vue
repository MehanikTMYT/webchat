<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-content text-center py-4">
        <p class="text-secondary">
          © {{ currentYear }} Гибридный чат-бот. Все права защищены.
        </p>
        <p class="text-secondary text-sm mt-1">
          Версия 1.0.0 | Локальная обработка с приватностью
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentYear: Number
})
</script>

<style scoped>
.footer {
  height: var(--footer-height);
  background-color: var(--card-background);
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.footer-content {
  color: var(--text-secondary);
}

.text-sm {
  font-size: 0.875rem;
}
</style>
