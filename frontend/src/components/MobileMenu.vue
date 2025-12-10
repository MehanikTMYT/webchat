<template>
  <div class="mobile-menu" :class="{ 'open': isOpen }">
    <div class="menu-content">
      <div class="menu-header">
        <h3 class="menu-title">Меню</h3>
        <button class="menu-close" @click="onClose">
          <i class="material-icons">close</i>
        </button>
      </div>
      
      <div class="menu-items">
        <router-link to="/chat" class="menu-item" @click="onClose">
          <i class="material-icons">chat</i>
          Чат
        </router-link>
        <router-link to="/characters" class="menu-item" @click="onClose">
          <i class="material-icons">person</i>
          Персонажи
        </router-link>
        <router-link to="/settings" class="menu-item" @click="onClose">
          <i class="material-icons">settings</i>
          Настройки
        </router-link>
        <button class="menu-item logout-item" @click="onLogout">
          <i class="material-icons">logout</i>
          Выход
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'logout', 'new-chat'])

const onClose = () => {
  emit('close')
}

const onLogout = () => {
  emit('logout')
  onClose()
}
</script>

<style scoped>
.mobile-menu {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.mobile-menu.open {
  opacity: 1;
  pointer-events: auto;
}

.menu-content {
  background-color: var(--card-background);
  border-radius: var(--border-radius-large);
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.menu-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-title {
  font-size: 1.25rem;
  font-weight: 600;
}

.menu-close {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
}

.menu-items {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: var(--border-radius-medium);
  text-decoration: none;
  color: var(--text-color);
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.menu-item:hover {
  background-color: var(--border-color);
}

.menu-item i {
  font-size: 1.25rem;
}

.logout-item {
  color: var(--danger-color);
  margin-top: 1rem;
  border-top: 1px solid var(--border-color);
  padding-top: 1rem;
}

@media (min-width: 769px) {
  .mobile-menu {
    display: none;
  }
}
</style>
