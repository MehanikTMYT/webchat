import { defineStore } from 'pinia'
import { ref, computed, onMounted, onUnmounted } from 'vue'

export const useNetworkStore = defineStore('network', () => {
  const isOnline = ref(navigator.onLine)
  const connectionType = ref(navigator.connection?.effectiveType || 'unknown')
  const downlink = ref(navigator.connection?.downlink || 0)
  const rtt = ref(navigator.connection?.rtt || 0)
  const lastOnlineCheck = ref(new Date())
  const connectionStatus = ref('checking')
  const pingLatency = ref(0)
  
  // Вычисляемые свойства
  const connectionQuality = computed(() => {
    if (!isOnline.value) return 'offline'
    if (pingLatency.value > 500 || downlink.value < 1) return 'poor'
    if (pingLatency.value > 200 || downlink.value < 5) return 'fair'
    return 'good'
  })
  
  const isSlowConnection = computed(() => {
    return downlink.value < 2 || rtt.value > 300
  })
  
  const getStatusText = computed(() => {
    if (!isOnline.value) return 'Офлайн'
    const qualities = {
      'offline': 'Нет подключения',
      'poor': 'Плохое соединение',
      'fair': 'Удовлетворительное соединение',
      'good': 'Хорошее соединение'
    }
    return qualities[connectionQuality.value] || 'Проверка соединения...'
  })
  
  // Методы
  const updateConnectionInfo = () => {
    if (navigator.connection) {
      connectionType.value = navigator.connection.effectiveType
      downlink.value = navigator.connection.downlink
      rtt.value = navigator.connection.rtt
    }
  }
  
  const checkConnection = async () => {
    try {
      const startTime = Date.now()
      const response = await fetch('/api/health', {
        method: 'GET',
        mode: 'no-cors',
        cache: 'no-cache',
        timeout: 5000
      })
      const endTime = Date.now()
      
      pingLatency.value = endTime - startTime
      connectionStatus.value = 'connected'
      lastOnlineCheck.value = new Date()
      
      return true
    } catch (error) {
      console.warn('Connection check failed:', error)
      connectionStatus.value = 'disconnected'
      return false
    }
  }
  
  const initialize = () => {
    // Слушатели событий сети
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    // Обновление информации о соединении при изменении
    if (navigator.connection) {
      navigator.connection.addEventListener('change', updateConnectionInfo)
    }
    
    // Периодическая проверка соединения
    const checkInterval = setInterval(() => {
      if (isOnline.value) {
        checkConnection()
      }
    }, 30000) // Каждые 30 секунд
    
    // Первоначальная проверка
    checkConnection()
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      if (navigator.connection) {
        navigator.connection.removeEventListener('change', updateConnectionInfo)
      }
      clearInterval(checkInterval)
    }
  }
  
  const handleOnline = () => {
    isOnline.value = true
    lastOnlineCheck.value = new Date()
    checkConnection()
  }
  
  const handleOffline = () => {
    isOnline.value = false
    connectionStatus.value = 'offline'
  }
  
  const forceReconnect = async () => {
    connectionStatus.value = 'reconnecting'
    const result = await checkConnection()
    if (result) {
      connectionStatus.value = 'connected'
    } else {
      connectionStatus.value = 'disconnected'
    }
    return result
  }
  
  const getNetworkInfo = () => {
    return {
      isOnline: isOnline.value,
      connectionType: connectionType.value,
      downlink: downlink.value,
      rtt: rtt.value,
      pingLatency: pingLatency.value,
      connectionQuality: connectionQuality.value,
      lastCheck: lastOnlineCheck.value,
      status: connectionStatus.value
    }
  }
  
  return {
    isOnline,
    connectionType,
    downlink,
    rtt,
    pingLatency,
    connectionStatus,
    lastOnlineCheck,
    connectionQuality,
    isSlowConnection,
    getStatusText,
    updateConnectionInfo,
    checkConnection,
    initialize,
    forceReconnect,
    getNetworkInfo
  }
})
