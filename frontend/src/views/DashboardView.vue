<template>
  <div class="dashboard-container">
    <div class="card">
      <div class="card-header">
        <h2>Добро пожаловать в Гибридный Чат-бот</h2>
      </div>
      <div class="card-body">
        <p>Ваш локальный чат-бот с приватностью и производительностью готов к работе!</p>
        <div class="mt-4">
          <router-link to="/chat" class="btn btn-primary">
            <i class="material-icons">chat</i> Начать чат
          </router-link>
        </div>
      </div>
      <div class="card-footer">
        <p class="text-secondary">Режим сети: {{ networkMode }} | Статус инференса: {{ inferenceStatus }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const networkMode = ref('relay')
const inferenceStatus = ref('ожидание')

onMounted(async () => {
  try {
    const response = await fetch('/api/health')
    if (response.ok) {
      const data = await response.json()
      networkMode.value = data.connection_mode
      inferenceStatus.value = data.network_config.inference_endpoint ? 'активен' : 'неактивен'
    }
  } catch (error) {
    console.error('Ошибка получения статуса:', error)
    inferenceStatus.value = 'ошибка'
  }
})
</script>

<style scoped>
.dashboard-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.mt-4 {
  margin-top: 1rem;
}
.text-secondary {
  color: var(--text-secondary);
  font-size: 0.875rem;
}
</style>
