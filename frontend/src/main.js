import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/styles/main.css'

// Импорт маршрутов
import { routes } from './router'

// Создание приложения
const app = createApp(App)

// Создание и настройка Pinia (управление состоянием)
const pinia = createPinia()
app.use(pinia)

// Регистрация глобальных свойств
app.config.globalProperties.$api = {
  baseUrl: import.meta.env.VITE_API_BASE || '/api/',
  wsBaseUrl: import.meta.env.VITE_WS_BASE || 'ws://localhost:8050/ws/'
}

// Функция для получения токена из localStorage
const getStoredToken = () => {
  return localStorage.getItem('chatbot_token')
}

// Проверка аутентификации перед каждым переходом
const authGuard = (to, from, next) => {
  const token = getStoredToken()
  
  if (to.meta.requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresGuest && token) {
    next({ name: 'chat' })
  } else {
    next()
  }
}

// Создание роутера
const router = createRouter({
  history: createWebHistory(),
  routes
})

// Применение guard к маршрутам
router.beforeEach(authGuard)

// Глобальный обработчик ошибок
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err, info)
  // Здесь можно добавить отправку ошибок в лог или оповещение пользователя
}

// Глобальный обработчик необработанных промисов
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  event.preventDefault()
})

// Инициализация приложения
app.use(router)

// Автоматическое обновление токена при загрузке страницы
const initApp = async () => {
  const token = getStoredToken()
  if (token) {
    try {
      const response = await fetch(`${app.config.globalProperties.$api.baseUrl}auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('chatbot_token', data.access_token)
      } else {
        localStorage.removeItem('chatbot_token')
      }
    } catch (error) {
      console.error('Error refreshing token:', error)
      localStorage.removeItem('chatbot_token')
    }
  }
  
  app.mount('#app')
}

// Запуск инициализации
initApp()

// Добавление обработчика offline/online событий
window.addEventListener('online', () => {
  console.log('Вернулись в онлайн-режим')
  // Здесь можно реализовать синхронизацию данных
})

window.addEventListener('offline', () => {
  console.log('Перешли в офлайн-режим')
  // Здесь можно показать уведомление пользователю
})

export default app