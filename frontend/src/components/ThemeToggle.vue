<template>
  <button class="theme-toggle" @click="onToggle">
    <i class="material-icons">{{ isDarkMode ? 'light_mode' : 'dark_mode' }}</i>
  </button>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  isDarkMode: Boolean
})

const emit = defineEmits(['toggle'])

const onToggle = () => {
  emit('toggle')
}
</script>

<style scoped>
.theme-toggle {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
}

.theme-toggle:hover {
  background-color: var(--border-color);
}
</style>
