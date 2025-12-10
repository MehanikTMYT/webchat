<template>
  <div class="settings-container">
    <div class="card">
      <div class="card-header">
        <h2 class="text-2xl font-bold flex items-center gap-2">
          <i class="material-icons">settings</i>
          Настройки
        </h2>
      </div>
      
      <div class="card-body">
        <div class="settings-section">
          <h3 class="settings-section-title">Профиль</h3>
          <div class="form-group">
            <label class="form-label">Имя пользователя</label>
            <div class="settings-value">
              {{ authStore.user?.username || 'Не указано' }}
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Дата регистрации</label>
            <div class="settings-value">
              {{ formatDate(authStore.user?.created_at) || 'Неизвестно' }}
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h3 class="settings-section-title">Внешний вид</h3>
          <div class="form-group">
            <label class="form-label">Тема</label>
            <div class="flex gap-4 mt-2">
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="system" 
                  v-model="theme" 
                  @change="updateTheme"
                >
                <div class="theme-preview system">
                  <div class="theme-preview-light"></div>
                  <div class="theme-preview-dark"></div>
                </div>
                <span>Системная</span>
              </label>
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="light" 
                  v-model="theme" 
                  @change="updateTheme"
                >
                <div class="theme-preview light">
                  <div class="theme-preview-content"></div>
                </div>
                <span>Светлая</span>
              </label>
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="dark" 
                  v-model="theme" 
                  @change="updateTheme"
                >
                <div class="theme-preview dark">
                  <div class="theme-preview-content"></div>
                </div>
                <span>Темная</span>
              </label>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h3 class="settings-section-title">Уведомления</h3>
          <div class="form-group">
            <label class="form-label">Звуковые уведомления</label>
            <label class="switch">
              <input type="checkbox" v-model="notifications.sound" @change="saveSettings">
              <span class="slider"></span>
            </label>
          </div>
          <div class="form-group">
            <label class="form-label">Уведомления о новых сообщениях</label>
            <label class="switch">
              <input type="checkbox" v-model="notifications.messages" @change="saveSettings">
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <div class="settings-section">
          <h3 class="settings-section-title">Безопасность</h3>
          <div class="form-group">
            <label class="form-label">Сменить пароль</label>
            <button class="btn btn-outline" @click="showChangePassword">
              <i class="material-icons">lock</i> Изменить пароль
            </button>
          </div>
          <div class="form-group">
            <label class="form-label">Активные сессии</label>
            <div class="active-sessions">
              <div v-for="(session, index) in activeSessions" :key="index" class="session-item">
                <div class="session-info">
                  <span class="session-device">{{ session.device }}</span>
                  <span class="session-ip">{{ session.ip }}</span>
                  <span class="session-time">{{ formatDate(session.last_active) }}</span>
                </div>
                <button 
                  v-if="!session.current" 
                  class="btn btn-sm btn-danger" 
                  @click="terminateSession(session.id)"
                >
                  Завершить
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h3 class="settings-section-title">Данные и приватность</h3>
          <div class="form-group">
            <label class="form-label">Экспорт данных</label>
            <button class="btn btn-outline" @click="exportData">
              <i class="material-icons">download</i> Скачать все данные
            </button>
          </div>
          <div class="form-group">
            <label class="form-label">Очистка истории</label>
            <button class="btn btn-danger" @click="clearHistory">
              <i class="material-icons">delete</i> Удалить всю историю чатов
            </button>
          </div>
        </div>
      </div>

      <div class="card-footer">
        <button class="btn btn-primary" @click="saveSettings">
          <i class="material-icons">save</i> Сохранить изменения
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const chatStore = useChatStore()
const router = useRouter()

const theme = ref('system')
const notifications = ref({
  sound: true,
  messages: true
})
const activeSessions = ref([])
const showPasswordModal = ref(false)

// Загрузка настроек при монтировании
onMounted(async () => {
  loadSettings()
  await loadActiveSessions()
})

const loadSettings = () => {
  const savedTheme = localStorage.getItem('darkMode')
  if (savedTheme !== null) {
    theme.value = savedTheme === 'true' ? 'dark' : savedTheme === 'false' ? 'light' : 'system'
  }
  
  const savedNotifications = JSON.parse(localStorage.getItem('chatbot_notifications') || '{}')
  notifications.value = {
    sound: savedNotifications.sound !== undefined ? savedNotifications.sound : true,
    messages: savedNotifications.messages !== undefined ? savedNotifications.messages : true
  }
}

const loadActiveSessions = async () => {
  try {
    const response = await fetch('/api/auth/sessions', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      const sessions = await response.json()
      activeSessions.value = sessions.map(session => ({
        ...session,
        current: session.session_id === localStorage.getItem('chatbot_session_id')
      }))
    }
  } catch (error) {
    console.error('Error loading active sessions:', error)
  }
}

const updateTheme = () => {
  const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches
  
  if (theme.value === 'system') {
    document.documentElement.classList.toggle('dark', systemPreference)
    localStorage.removeItem('darkMode')
  } else if (theme.value === 'dark') {
    document.documentElement.classList.add('dark')
    localStorage.setItem('darkMode', 'true')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('darkMode', 'false')
  }
}

const saveSettings = () => {
  localStorage.setItem('chatbot_notifications', JSON.stringify(notifications.value))
  // Здесь можно добавить отправку настроек на сервер
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const showChangePassword = () => {
  alert('Функция изменения пароля будет доступна в следующем обновлении')
}

const terminateSession = async (sessionId) => {
  if (!confirm('Вы уверены, что хотите завершить эту сессию?')) return
  
  try {
    const response = await fetch(`/api/auth/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      activeSessions.value = activeSessions.value.filter(s => s.id !== sessionId)
      alert('Сессия успешно завершена')
    } else {
      throw new Error('Не удалось завершить сессию')
    }
  } catch (error) {
    console.error('Error terminating session:', error)
    alert('Ошибка при завершении сессии')
  }
}

const exportData = () => {
  if (!confirm('Вы хотите скачать все ваши данные, включая историю чатов?')) return
  
  try {
    const data = {
      user: authStore.user,
      sessions: chatStore.sessions,
      messages: chatStore.messages
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chatbot-data-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    alert('Данные успешно экспортированы')
  } catch (error) {
    console.error('Error exporting data:', error)
    alert('Ошибка при экспорте данных')
  }
}

const clearHistory = async () => {
  if (!confirm('Вы уверены, что хотите удалить ВСЮ историю чатов? Это действие нельзя отменить.')) return
  
  try {
    const response = await fetch('/api/chat/clear-history', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      chatStore.messages = []
      chatStore.sessions = []
      await chatStore.loadSessions()
      alert('История чатов успешно очищена')
    } else {
      throw new Error('Не удалось очистить историю')
    }
  } catch (error) {
    console.error('Error clearing history:', error)
    alert('Ошибка при очистке истории')
  }
}
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.settings-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.settings-section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-color);
}

.settings-value {
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.theme-option input {
  display: none;
}

.theme-preview {
  width: 60px;
  height: 40px;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  display: flex;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.theme-preview.system {
  position: relative;
}

.theme-preview.system::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to right, #f8fafc 50%, #1e293b 50%);
}

.theme-preview.light {
  background-color: #f8fafc;
  border: 1px solid var(--border-color);
}

.theme-preview.light .theme-preview-content {
  width: 100%;
  height: 100%;
  background-color: #ffffff;
}

.theme-preview.dark {
  background-color: #0f172a;
  border: 1px solid var(--border-color);
}

.theme-preview.dark .theme-preview-content {
  width: 100%;
  height: 100%;
  background-color: #1e293b;
}

.theme-option span {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.theme-option input:checked + .theme-preview + span {
  color: var(--primary-color);
  font-weight: 500;
}

.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.active-sessions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background-color: var(--card-background);
  border-radius: var(--border-radius-medium);
  border: 1px solid var(--border-color);
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.session-device {
  font-weight: 500;
}

.session-ip {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.session-time {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .settings-container {
    margin: 1rem auto;
  }
  
  .theme-option {
    flex-direction: row;
    gap: 1rem;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0.5rem 0;
  }
  
  .theme-preview {
    margin-bottom: 0;
  }
}
</style>
