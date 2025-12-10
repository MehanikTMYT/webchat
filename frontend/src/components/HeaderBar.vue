<template>
  <header class="header">
    <div class="container flex items-center justify-between h-full">
      <div class="logo flex items-center gap-2">
        <router-link to="/" class="logo-link">
          <div class="logo-icon-container">
            <i class="material-icons logo-icon">smart_toy</i>
          </div>
          <span class="logo-text">Чат-бот</span>
        </router-link>
      </div>
      
      <div class="header-actions flex items-center gap-3">
        <!-- Навигация для десктопа -->
        <nav class="desktop-nav hidden-mobile">
          <ul class="nav-list flex gap-4">
            <li>
              <router-link to="/chat" class="nav-link">
                <i class="material-icons">chat</i>
                <span>Чат</span>
              </router-link>
            </li>
            <li>
              <router-link to="/characters" class="nav-link">
                <i class="material-icons">person</i>
                <span>Персонажи</span>
              </router-link>
            </li>
            <li>
              <router-link to="/settings" class="nav-link">
                <i class="material-icons">settings</i>
                <span>Настройки</span>
              </router-link>
            </li>
          </ul>
        </nav>
        
        <!-- Статус сети -->
        <div class="network-status" @click="toggleNetworkInfo">
          <div class="status-indicator" :class="networkStatusClass"></div>
          <span class="status-text hidden-mobile">{{ networkStatusText }}</span>
        </div>
        
        <!-- Переключатель темы -->
        <button class="theme-toggle" @click="toggleTheme" :aria-label="`Переключить ${isDarkMode ? 'светлую' : 'темную'} тему`">
          <i class="material-icons theme-icon">
            {{ isDarkMode ? 'light_mode' : 'dark_mode' }}
          </i>
        </button>
        
        <!-- Кнопка пользователя -->
        <div class="user-menu relative" v-if="authStore.isAuthenticated">
          <button class="user-button" @click="toggleUserMenu">
            <div class="user-avatar">
              <i class="material-icons">person</i>
            </div>
            <span class="user-name hidden-mobile">{{ authStore.user?.username || 'Пользователь' }}</span>
          </button>
          <div class="user-dropdown" v-if="isUserMenuOpen">
            <div class="dropdown-arrow"></div>
            <div class="dropdown-content">
              <router-link to="/settings" class="dropdown-item">
                <i class="material-icons">settings</i>
                Настройки
              </router-link>
              <button class="dropdown-item logout-item" @click="handleLogout">
                <i class="material-icons">logout</i>
                Выход
              </button>
            </div>
          </div>
        </div>
        
        <!-- Кнопка входа -->
        <router-link to="/login" class="login-button" v-else>
          <i class="material-icons">login</i>
          <span class="hidden-mobile">Вход</span>
        </router-link>
        
        <!-- Мобильное меню -->
        <div class="mobile-menu-button block-mobile" @click="onToggleMobileMenu">
          <i class="material-icons">menu</i>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно с информацией о сети -->
    <div v-if="showNetworkInfo" class="network-modal" @click="showNetworkInfo = false">
      <div class="network-modal-content" @click.stop>
        <h3 class="modal-title">Состояние сети</h3>
        <div class="network-details">
          <div class="detail-row">
            <span class="detail-label">Статус:</span>
            <span class="detail-value" :class="networkStatusClass">{{ networkStatusText }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Тип подключения:</span>
            <span class="detail-value">{{ networkStore.connectionType || 'Неизвестно' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Скорость:</span>
            <span class="detail-value">{{ networkStore.downlink }} Mbps</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Задержка:</span>
            <span class="detail-value">{{ networkStore.pingLatency }} мс</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Последняя проверка:</span>
            <span class="detail-value">{{ formatLastCheck() }}</span>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary modal-button" @click="forceReconnect">
            Переподключиться
          </button>
          <button class="btn btn-outline modal-button" @click="showNetworkInfo = false">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNetworkStore } from '../stores/network'
import { useThemeStore } from '../stores/theme'

const router = useRouter()
const authStore = useAuthStore()
const networkStore = useNetworkStore()
const themeStore = useThemeStore()

const isUserMenuOpen = ref(false)
const showNetworkInfo = ref(false)
const isMobile = ref(window.innerWidth < 768)

// Вычисляемые свойства
const isDarkMode = computed(() => themeStore.isDarkMode)
const networkStatusClass = computed(() => {
  if (!networkStore.isOnline) return 'status-offline'
  if (networkStore.connectionQuality === 'poor') return 'status-poor'
  if (networkStore.connectionQuality === 'fair') return 'status-fair'
  return 'status-good'
})

const networkStatusText = computed(() => {
  if (!networkStore.isOnline) return 'Офлайн'
  const qualities = {
    'poor': 'Плохое',
    'fair': 'Среднее',
    'good': 'Хорошее'
  }
  return `${qualities[networkStore.connectionQuality] || 'Хорошее'} соединение`
})

// Методы
const toggleTheme = () => {
  themeStore.toggleTheme()
}

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    isUserMenuOpen.value = false
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    alert('Ошибка при выходе из системы')
  }
}

const toggleNetworkInfo = () => {
  showNetworkInfo.value = !showNetworkInfo.value
}

const forceReconnect = async () => {
  try {
    await networkStore.forceReconnect()
    showNotification('Переподключение выполнено успешно!', 'success')
  } catch (error) {
    console.error('Reconnection failed:', error)
    showNotification('Ошибка переподключения', 'error')
  }
}

const formatLastCheck = () => {
  if (!networkStore.lastOnlineCheck) return 'Никогда'
  const diff = new Date() - new Date(networkStore.lastOnlineCheck)
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Только что'
  if (minutes < 60) return `${minutes} мин назад`
  const hours = Math.floor(minutes / 60)
  return `${hours} ч назад`
}

const showNotification = (message, type = 'info') => {
  const event = new CustomEvent('notification', {
    detail: { message, type }
  })
  document.dispatchEvent(event)
}

const updateIsMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const onToggleMobileMenu = () => {
  const event = new CustomEvent('toggle-mobile-menu')
  document.dispatchEvent(event)
}

// Хуки жизненного цикла
onMounted(() => {
  // Закрытие меню пользователя при клике вне его
  const handleClickOutside = (event) => {
    if (!event.target.closest('.user-menu')) {
      isUserMenuOpen.value = false
    }
  }
  
  window.addEventListener('click', handleClickOutside)
  
  // Слушатель изменения размера окна
  window.addEventListener('resize', updateIsMobile)
  
  // Инициализация сети
  networkStore.initialize()
  
  // Очистка при размонтировании
  onUnmounted(() => {
    window.removeEventListener('click', handleClickOutside)
    window.removeEventListener('resize', updateIsMobile)
  })
})
</script>

<style scoped>
.header {
  height: var(--header-height);
  background-color: var(--card-background);
  box-shadow: 0 2px 4px var(--shadow-color);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  height: 100%;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-color);
  font-weight: 600;
  font-size: 1.25rem;
}

.logo-icon-container {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-color);
  color: white;
  border-radius: 8px;
}

.logo-icon {
  font-size: 1.25rem;
}

.logo-text {
  line-height: 1;
}

.header-actions {
  height: 100%;
}

.desktop-nav ul {
  list-style: none;
  margin: 0;
  padding: 0;
  height: 100%;
  display: flex;
  align-items: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color);
  text-decoration: none;
  padding: 0.5rem 0.75rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
}

.nav-link:hover, .nav-link.router-link-active {
  background-color: var(--border-color);
  color: var(--primary-color);
}

.nav-link i {
  font-size: 1.1rem;
}

.network-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
}

.network-status:hover {
  background-color: var(--border-color);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-offline {
  background-color: var(--danger-color);
  box-shadow: 0 0 4px rgba(231, 76, 60, 0.5);
}

.status-poor {
  background-color: var(--warning-color);
  box-shadow: 0 0 4px rgba(243, 156, 18, 0.5);
}

.status-fair {
  background-color: #f39c12;
  box-shadow: 0 0 4px rgba(243, 156, 18, 0.5);
}

.status-good {
  background-color: var(--success-color);
  box-shadow: 0 0 4px rgba(46, 204, 113, 0.5);
}

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

.theme-icon {
  font-size: 1.25rem;
}

.user-menu {
  position: relative;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
}

.user-button:hover {
  background-color: var(--border-color);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.user-name {
  font-size: 0.9rem;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  min-width: 200px;
  z-index: 1001;
}

.dropdown-arrow {
  position: absolute;
  top: -8px;
  right: 12px;
  width: 16px;
  height: 16px;
  background-color: var(--card-background);
  transform: rotate(45deg);
  z-index: 999;
  box-shadow: -2px -2px 4px rgba(0,0,0,0.05);
}

.dropdown-content {
  background-color: var(--card-background);
  border-radius: var(--border-radius-large);
  box-shadow: 0 4px 12px var(--shadow-color);
  padding: 0.5rem;
  border: 1px solid var(--border-color);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: var(--border-radius-medium);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: var(--text-color);
  border: none;
  font-weight: 500;
  font-size: 0.95rem;
}

.dropdown-item:hover {
  background-color: var(--border-color);
}

.dropdown-item i {
  font-size: 1.1rem;
  width: 20px;
}

.logout-item {
  color: var(--danger-color);
  margin-top: 0.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.login-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
  text-decoration: none;
  font-weight: 500;
}

.login-button:hover {
  background-color: var(--border-color);
}

.login-button i {
  font-size: 1.25rem;
}

.mobile-menu-button {
  display: none;
  cursor: pointer;
  color: var(--text-color);
  font-size: 1.5rem;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
}

.mobile-menu-button:hover {
  background-color: var(--border-color);
}

.network-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.3s ease;
}

.network-modal-content {
  background-color: var(--card-background);
  border-radius: var(--border-radius-large);
  width: 90%;
  max-width: 400px;
  padding: 1.5rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  max-height: 80vh;
  overflow-y: auto;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  text-align: center;
  color: var(--text-color);
}

.network-details {
  margin-bottom: 1.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.detail-value {
  font-weight: 500;
  color: var(--text-color);
}

.detail-value.status-poor, .detail-value.status-offline {
  color: var(--danger-color);
}

.detail-value.status-fair {
  color: var(--warning-color);
}

.detail-value.status-good {
  color: var(--success-color);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.modal-button {
  flex: 1;
  padding: 0.75rem;
  font-weight: 500;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .hidden-mobile {
    display: none !important;
  }
  
  .block-mobile {
    display: block !important;
  }
  
  .desktop-nav {
    display: none;
  }
  
  .mobile-menu-button {
    display: block;
  }
  
  .logo-text {
    display: none;
  }
  
  .user-name {
    display: none;
  }
  
  .status-text {
    display: none;
  }
  
  .header-actions {
    gap: 0.5rem;
  }
  
  .user-button, .theme-toggle, .network-status, .login-button {
    padding: 0.4rem;
  }
  
  .logo-icon-container {
    width: 28px;
    height: 28px;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 0.75rem;
  }
  
  .header-actions {
    gap: 0.25rem;
  }
  
  .mobile-menu-button {
    padding: 0.3rem;
  }
}
</style>