<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useChatStore } from './stores/chat'
import { useNetworkStore } from './stores/network'
import NetworkStatus from './components/NetworkStatus.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import MobileMenu from './components/MobileMenu.vue'
import HeaderBar from './components/HeaderBar.vue'
import FooterBar from './components/FooterBar.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const networkStore = useNetworkStore()

const isMobileMenuOpen = ref(false)
const isDarkMode = ref(false)
const isLoading = ref(true)
const notification = ref(null)

// Проверка авторизации при загрузке
onMounted(async () => {
  // Проверка темной темы
  isDarkMode.value = localStorage.getItem('darkMode') === 'true' || 
                    (window.matchMedia('(prefers-color-scheme: dark)').matches && !localStorage.getItem('darkMode'))
  
  // Установка темы
  updateTheme()
  
  // Подписка на события сети
  networkStore.initialize()
  
  // Проверка аутентификации
  if (authStore.token) {
    try {
      await authStore.verifyToken()
    } catch (error) {
      console.error('Authentication failed:', error)
      authStore.logout()
    }
  }
  
  // Загрузка сессий чата
  if (authStore.isAuthenticated) {
    try {
      await chatStore.loadSessions()
    } catch (error) {
      console.error('Failed to load chat sessions:', error)
      showNotification('Не удалось загрузить сессии чата', 'error')
    }
  }
  
  isLoading.value = false
  
  // Слушатель изменения темы системы
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('darkMode')) {
      isDarkMode.value = e.matches
      updateTheme()
    }
  })
})

onUnmounted(() => {
  window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', () => {})
})

// Обновление темы
const updateTheme = () => {
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('darkMode', 'true')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('darkMode', 'false')
  }
}

// Переключение темы
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  updateTheme()
}

// Показ уведомления
const showNotification = (message, type = 'info') => {
  notification.value = { message, type, id: Date.now() }
  setTimeout(() => {
    notification.value = null
  }, 5000)
}

// Обработка выхода
const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
    showNotification('Вы успешно вышли из системы')
  } catch (error) {
    console.error('Logout failed:', error)
    showNotification('Ошибка при выходе из системы', 'error')
  }
}

// Проверка, является ли текущий маршрут защищенным
const isAuthRoute = computed(() => {
  return ['login', 'register', 'not-found'].includes(route.name)
})

// Проверка, скрыть ли sidebar на мобильных
const hideSidebarOnMobile = computed(() => {
  return isAuthRoute.value || isMobileMenuOpen.value
})

// Получение текущего года для футера
const currentYear = computed(() => new Date().getFullYear())

// Обработка открытия мобильного меню
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}
</script>

<template>
  <div class="app-container" :class="{ 'dark': isDarkMode }">
    <!-- Лоадер при инициализации -->
    <div v-if="isLoading" class="loader-overlay">
      <div class="loader"></div>
    </div>

    <!-- Уведомления -->
    <div v-if="notification" class="notification" :class="notification.type">
      {{ notification.message }}
    </div>

    <!-- Верхний бар -->
    <HeaderBar 
      :is-authenticated="authStore.isAuthenticated" 
      :user="authStore.user" 
      :is-mobile-menu-open="isMobileMenuOpen"
      @toggle-mobile-menu="toggleMobileMenu"
      @logout="handleLogout"
    />

    <!-- Основной контент -->
    <main class="main-content">
      <div class="container">
        <div class="content-wrapper">
          <!-- Сайдбар (скрыт на мобильных при определенных маршрутах) -->
          <aside v-if="authStore.isAuthenticated && !hideSidebarOnMobile" class="sidebar">
            <div class="sidebar-header">
              <h2 class="sidebar-title">Чаты</h2>
              <button class="new-chat-btn" @click="chatStore.createSession()">
                <i class="material-icons">add</i> Новый чат
              </button>
            </div>
            
            <div class="sessions-list">
              <div 
                v-for="session in chatStore.sessions" 
                :key="session.id" 
                class="session-item"
                :class="{ active: session.id === $route.params.sessionId }"
                @click="router.push(`/chat/${session.id}`)"
              >
                <div class="session-title">{{ session.title || 'Новый чат' }}</div>
                <div class="session-meta">
                  <span class="session-time">{{ new Date(session.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</span>
                  <button class="delete-session" @click.stop="chatStore.deleteSession(session.id)">
                    <i class="material-icons">close</i>
                  </button>
                </div>
              </div>
            </div>

            <div class="sidebar-footer">
              <div class="network-status">
                <NetworkStatus />
              </div>
              <div class="theme-toggle">
                <ThemeToggle :is-dark-mode="isDarkMode" @toggle="toggleTheme" />
              </div>
            </div>
          </aside>

          <!-- Основная область контента -->
          <div class="content-area" :class="{ 'full-width': !authStore.isAuthenticated || hideSidebarOnMobile }">
            <router-view 
              :key="$route.fullPath" 
              @notification="showNotification"
            />
          </div>
        </div>
      </div>
    </main>

    <!-- Мобильное меню -->
    <MobileMenu 
      v-if="authStore.isAuthenticated" 
      :is-open="isMobileMenuOpen" 
      @close="toggleMobileMenu"
      @logout="handleLogout"
      @new-chat="chatStore.createSession()"
    />

    <!-- Футер -->
    <FooterBar :current-year="currentYear" />
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f8fafc;
  transition: background-color 0.3s ease;
}

.dark .app-container {
  background-color: #0f172a;
  color: #f1f5f9;
}

.loader-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loader {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: slideIn 0.3s ease-out, fadeOut 0.5s ease-in 4.5s;
}

.notification.info {
  background-color: #3498db;
}

.notification.success {
  background-color: #2ecc71;
}

.notification.warning {
  background-color: #f39c12;
}

.notification.error {
  background-color: #e74c3c;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

.main-content {
  flex: 1;
  padding-top: 60px; /* Высота хедера */
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.content-wrapper {
  display: flex;
  gap: 1.5rem;
}

.sidebar {
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  height: calc(100vh - 100px);
  overflow-y: auto;
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
}

.dark .sidebar {
  background-color: #1e293b;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.dark .sidebar-header {
  border-bottom-color: #334155;
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
}

.dark .sidebar-title {
  color: #f1f5f9;
}

.new-chat-btn {
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.new-chat-btn:hover {
  background: #2980b9;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #f8fafc;
}

.dark .session-item {
  background-color: #1e293b;
}

.session-item:hover {
  background-color: #e2e8f0;
  transform: translateX(4px);
}

.dark .session-item:hover {
  background-color: #334155;
}

.session-item.active {
  background-color: #bfdbfe;
  border-left: 3px solid #3498db;
}

.dark .session-item.active {
  background-color: #1e40af;
}

.session-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #64748b;
}

.session-time {
  color: #64748b;
}

.delete-session {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item:hover .delete-session {
  opacity: 1;
}

.delete-session:hover {
  color: #e74c3c;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.dark .sidebar-footer {
  border-top-color: #334155;
}

.network-status, .theme-toggle {
  margin-bottom: 0.5rem;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.content-area.full-width {
  width: 100%;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    bottom: 0;
    transform: translateX(-100%);
    z-index: 100;
  }
  
  .sidebar.show {
    transform: translateX(0);
  }
  
  .content-wrapper {
    flex-direction: column;
  }
  
  .content-area {
    width: 100%;
  }
  
  .main-content {
    padding-top: 60px;
  }
}

@media (max-width: 480px) {
  .sidebar-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .notification {
    width: calc(100% - 40px);
    text-align: center;
    left: 50%;
    transform: translateX(-50%);
  }
}
</style>