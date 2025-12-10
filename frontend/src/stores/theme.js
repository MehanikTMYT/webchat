import { defineStore } from 'pinia'
import { ref, computed, onMounted } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDarkMode = ref(false)
  const prefersDark = ref(false)
  
  // Вычисляемое свойство для проверки системных настроек
  const systemPrefersDark = computed(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  
  // Инициализация темы при загрузке
  const initializeTheme = () => {
    // Загружаем сохраненную тему из localStorage
    const savedTheme = localStorage.getItem('darkMode')
    
    if (savedTheme !== null) {
      // Если тема была сохранена явно
      isDarkMode.value = savedTheme === 'true'
    } else {
      // Если тема не была сохранена, используем системные настройки
      isDarkMode.value = systemPrefersDark.value
      prefersDark.value = true
    }
    
    // Устанавливаем тему в DOM
    updateDocumentTheme()
    
    // Слушатель изменения системных настроек
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (prefersDark.value) {
        isDarkMode.value = e.matches
        updateDocumentTheme()
      }
    })
  }
  
  // Обновление темы в DOM
  const updateDocumentTheme = () => {
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
  
  // Переключение темы
  const toggleTheme = () => {
    // Если тема следовала системным настройкам, сохраняем явный выбор
    if (prefersDark.value) {
      prefersDark.value = false
    }
    
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem('darkMode', String(isDarkMode.value))
    updateDocumentTheme()
  }
  
  // Установка конкретной темы
  const setTheme = (dark) => {
    prefersDark.value = false
    isDarkMode.value = dark
    localStorage.setItem('darkMode', String(dark))
    updateDocumentTheme()
  }
  
  // Сброс к системным настройкам
  const resetToSystem = () => {
    prefersDark.value = true
    isDarkMode.value = systemPrefersDark.value
    localStorage.removeItem('darkMode')
    updateDocumentTheme()
  }
  
  // Получение текущего состояния темы
  const getThemeState = () => {
    return {
      isDarkMode: isDarkMode.value,
      isSystemPreference: prefersDark.value,
      systemTheme: systemPrefersDark.value ? 'dark' : 'light'
    }
  }
  
  // Хук для автоматической инициализации
  onMounted(() => {
    initializeTheme()
  })
  
  return {
    isDarkMode,
    prefersDark,
    systemPrefersDark,
    initializeTheme,
    toggleTheme,
    setTheme,
    resetToSystem,
    getThemeState,
    updateDocumentTheme
  }
})
