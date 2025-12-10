<template>
  <div class="chat-container flex flex-col h-full">
    <div class="chat-header p-4 border-b border-border-color">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button class="back-button" @click="handleBack" v-if="isMobile">
            <i class="material-icons">arrow_back</i>
          </button>
          <h1 class="text-xl font-bold flex items-center gap-2">
            <i class="material-icons">chat</i>
            <span class="session-title">{{ currentSession?.title || 'Новый чат' }}</span>
          </h1>
        </div>
        <div class="flex gap-2">
          <button 
            class="btn btn-outline action-button" 
            @click="handleRegenerate"
            :disabled="loadingResponse || messages.length === 0"
            title="Перегенерировать последний ответ"
          >
            <i class="material-icons">refresh</i>
            <span class="hidden-mobile">Перегенерировать</span>
          </button>
          <button 
            class="btn btn-outline action-button" 
            @click="handleNewSession"
            title="Новый чат"
          >
            <i class="material-icons">add</i>
            <span class="hidden-mobile">Новый чат</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="chat-messages flex-1 overflow-y-auto p-4" ref="messagesContainer">
      <div v-if="loadingInitial" class="flex justify-center py-8">
        <div class="loader"></div>
      </div>
      
      <div v-else-if="messages.length === 0 && !loadingInitial" class="empty-state text-center py-12">
        <div class="text-5xl mb-4 animate-bounce">💬</div>
        <h3 class="text-xl font-semibold mb-2">Начните диалог</h3>
        <p class="text-secondary mb-4">Задайте ваш первый вопрос, и я постараюсь вам помочь!</p>
        <div class="flex flex-col sm:flex-row justify-center gap-3">
          <button 
            class="btn btn-primary example-btn" 
            @click="handleExampleMessage('Привет! Как я могу вам помочь?')"
          >
            <i class="material-icons mr-1">handshake</i> Приветствие
          </button>
          <button 
            class="btn btn-outline example-btn" 
            @click="handleExampleMessage('Расскажи о себе и твоих возможностях.')"
          >
            <i class="material-icons mr-1">info</i> О боте
          </button>
        </div>
      </div>
      
      <transition-group name="message-list" tag="div">
        <div v-for="(message, index) in messages" :key="message.id" class="message-group mb-4">
          <div class="message" :class="{
            'message-user': message.role === 'user',
            'message-assistant': message.role === 'assistant',
            'message-error': message.error
          }">
            <div class="message-content">
              <div class="message-header">
                <i class="material-icons" :class="{
                  'text-primary': message.role === 'user',
                  'text-secondary': message.role === 'assistant'
                }">
                  {{ message.role === 'user' ? 'person' : 'smart_toy' }}
                </i>
                <span class="message-sender">
                  {{ message.role === 'user' ? 'Вы' : 'Ассистент' }}
                </span>
                <span class="message-time">
                  {{ formatTime(message.created_at) }}
                </span>
              </div>
              <div 
                class="message-body" 
                :class="{'message-markdown': message.role === 'assistant'}"
                v-html="formatMessage(message.content)"
              ></div>
              
              <div class="message-footer">
                <div class="message-actions" v-if="message.role === 'user' && !loadingResponse">
                  <button 
                    class="message-action copy-btn" 
                    @click="copyToClipboard(message.content)"
                    title="Копировать сообщение"
                  >
                    <i class="material-icons">content_copy</i>
                  </button>
                  <button 
                    class="message-action edit-btn" 
                    @click="handleEditMessage(message)"
                    title="Редактировать сообщение"
                  >
                    <i class="material-icons">edit</i>
                  </button>
                  <button 
                    class="message-action delete-btn" 
                    @click="handleDeleteMessage(message)"
                    title="Удалить сообщение"
                  >
                    <i class="material-icons">delete</i>
                  </button>
                </div>
                <div class="message-actions" v-if="message.role === 'assistant' && !loadingResponse">
                  <button 
                    class="message-action copy-btn" 
                    @click="copyToClipboard(message.content)"
                    title="Копировать ответ"
                  >
                    <i class="material-icons">content_copy</i>
                  </button>
                  <button 
                    class="message-action like-btn" 
                    @click="handleFeedback(message.id, 'positive')"
                    :class="{ active: message.feedback === 'positive' }"
                    title="Полезный ответ"
                  >
                    <i class="material-icons">thumb_up</i>
                  </button>
                  <button 
                    class="message-action dislike-btn" 
                    @click="handleFeedback(message.id, 'negative')"
                    :class="{ active: message.feedback === 'negative' }"
                    title="Не полезный ответ"
                  >
                    <i class="material-icons">thumb_down</i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition-group>
      
      <div v-if="loadingResponse" class="message message-assistant">
        <div class="message-content">
          <div class="message-header">
            <i class="material-icons text-secondary">smart_toy</i>
            <span>Ассистент</span>
            <span class="message-time">{{ currentTime }}</span>
          </div>
          <div class="message-body typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
      
      <div v-if="error" class="message message-error">
        <div class="message-content">
          <div class="message-header">
            <i class="material-icons text-danger">error</i>
            <span class="text-danger">Ошибка</span>
          </div>
          <div class="message-body">
            {{ error }}
          </div>
          <div class="message-footer">
            <button class="btn btn-sm btn-danger retry-btn" @click="retryLastAction">
              Повторить попытку
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input p-4 border-t border-border-color">
      <div class="input-container">
        <textarea
          v-model="inputMessage"
          class="input-field"
          placeholder="Введите ваше сообщение... (Enter для отправки, Shift+Enter для новой строки)"
          rows="1"
          @keypress.enter.exact.prevent="handleSendMessage"
          @input="handleInput"
          @keydown="handleKeyDown"
        ></textarea>
        <div class="input-actions">
          <button 
            class="action-button attachment-btn" 
            @click="handleAttachment"
            title="Прикрепить файл"
          >
            <i class="material-icons">attach_file</i>
          </button>
          <button 
            class="send-button" 
            @click="handleSendMessage"
            :disabled="!canSendMessage"
            :class="{ 'send-button-active': canSendMessage }"
            title="Отправить сообщение (Enter)"
          >
            <i class="material-icons">send</i>
          </button>
        </div>
      </div>
      <div v-if="inputMessage.length > 0" class="char-counter">
        {{ inputMessage.length }}/{{ maxMessageLength }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import { useNetworkStore } from '../stores/network'
import { useThemeStore } from '../stores/theme'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const authStore = useAuthStore()
const networkStore = useNetworkStore()
const themeStore = useThemeStore()

const sessionId = ref(route.params.sessionId || null)
const inputMessage = ref('')
const loadingResponse = ref(false)
const loadingInitial = ref(true)
const messagesContainer = ref(null)
const error = ref(null)
const lastAction = ref(null)
const isMobile = ref(window.innerWidth < 768)

const maxMessageLength = 2000
const currentTime = ref(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))

// Вычисляемые свойства
const currentSession = computed(() => {
  return chatStore.sessions.find(s => s.id === sessionId.value)
})

const messages = computed(() => {
  return chatStore.messages
    .filter(m => m.session_id === sessionId.value)
    .map(message => ({
      ...message,
      feedback: chatStore.messageFeedback[message.id] || null
    }))
})

const canSendMessage = computed(() => {
  return inputMessage.value.trim().length > 0 && 
         inputMessage.value.trim().length <= maxMessageLength &&
         !loadingResponse.value && 
         networkStore.isOnline
})

// Методы
const handleInput = (e) => {
  const textarea = e.target
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
  
  // Очистка ошибки при вводе
  if (error.value) {
    error.value = null
  }
}

const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    inputMessage.value = ''
  }
  
  // Shift+Enter для новой строки
  if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault()
    inputMessage.value += '\n'
  }
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatMessage = (content) => {
  if (!content) return ''
  
  // Обработка Markdown-подобного форматирования
  let formatted = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
    .replace(/\n/g, '<br>')
  
  // Обработка ссылок
  formatted = formatted.replace(
    /https?:\/\/[^\s]+/g, 
    url => `<a href="${url}" target="_blank" rel="noopener noreferrer" class="message-link">${url}</a>`
  )
  
  return formatted
}

const scrollToBottom = (smooth = false) => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    })
  }
}

const handleSendMessage = async () => {
  if (!canSendMessage.value) return
  
  const message = inputMessage.value.trim()
  if (message.length > maxMessageLength) {
    error.value = `Сообщение слишком длинное (максимум ${maxMessageLength} символов)`
    return
  }
  
  inputMessage.value = ''
  lastAction.value = { type: 'send_message', sessionId: sessionId.value, message }
  
  try {
    loadingResponse.value = true
    error.value = null
    
    // Если сессия не создана, создаем новую
    if (!sessionId.value) {
      const newSession = await chatStore.createSession()
      sessionId.value = newSession.id
      router.push({ name: 'chat-session', params: { sessionId: sessionId.value } })
    }
    
    // Отправляем сообщение
    await chatStore.sendMessage(sessionId.value, message)
    
    // Прокручиваем вниз после получения ответа
    await nextTick()
    scrollToBottom(true)
    
  } catch (err) {
    console.error('Error sending message:', err)
    error.value = 'Ошибка отправки сообщения: ' + (err.message || 'Попробуйте позже')
    
    // Если ошибка сети, удаляем последнее сообщение пользователя
    if (err.message?.includes('Network Error') || err.message?.includes('Failed to fetch')) {
      await chatStore.removeLastMessage(sessionId.value)
    }
  } finally {
    loadingResponse.value = false
  }
}

const handleNewSession = async () => {
  try {
    const newSession = await chatStore.createSession()
    sessionId.value = newSession.id
    router.push({ name: 'chat-session', params: { sessionId: sessionId.value } })
    inputMessage.value = ''
    error.value = null
  } catch (err) {
    console.error('Error creating new session:', err)
    error.value = 'Ошибка создания новой сессии'
  }
}

const handleExampleMessage = async (message) => {
  inputMessage.value = message
  await nextTick()
  handleSendMessage()
}

const handleRegenerate = async () => {
  if (!currentSession.value || messages.value.length === 0 || loadingResponse.value) return
  
  try {
    loadingResponse.value = true
    error.value = null
    lastAction.value = { type: 'regenerate', sessionId: sessionId.value }
    
    await chatStore.regenerateLastResponse(sessionId.value)
    await nextTick()
    scrollToBottom(true)
  } catch (err) {
    console.error('Error regenerating response:', err)
    error.value = 'Ошибка перегенерации ответа: ' + (err.message || 'Попробуйте позже')
  } finally {
    loadingResponse.value = false
  }
}

const handleEditMessage = async (message) => {
  if (message.role !== 'user' || loadingResponse.value) return
  
  const newContent = prompt('Редактировать сообщение:', message.content)
  if (newContent && newContent.trim() !== '' && newContent !== message.content) {
    try {
      loadingResponse.value = true
      error.value = null
      lastAction.value = { 
        type: 'edit_message', 
        sessionId: sessionId.value, 
        messageId: message.id, 
        oldContent: message.content,
        newContent: newContent 
      }
      
      await chatStore.editMessage(message.id, newContent.trim())
      await nextTick()
      scrollToBottom(true)
    } catch (err) {
      console.error('Error editing message:', err)
      error.value = 'Ошибка редактирования: ' + (err.message || 'Попробуйте позже')
    } finally {
      loadingResponse.value = false
    }
  }
}

const handleDeleteMessage = async (message) => {
  if (loadingResponse.value || !confirm('Удалить это сообщение и все последующие?')) return
  
  try {
    loadingResponse.value = true
    error.value = null
    lastAction.value = { 
      type: 'delete_message', 
      sessionId: sessionId.value, 
      messageId: message.id 
    }
    
    await chatStore.deleteMessage(message.id)
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error('Error deleting message:', err)
    error.value = 'Ошибка удаления: ' + (err.message || 'Попробуйте позже')
  } finally {
    loadingResponse.value = false
  }
}

const handleFeedback = async (messageId, feedback) => {
  try {
    await chatStore.setMessageFeedback(messageId, feedback)
  } catch (err) {
    console.error('Error setting feedback:', err)
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showNotification('Скопировано в буфер обмена!', 'success')
  } catch (err) {
    console.error('Error copying to clipboard:', err)
    showNotification('Ошибка копирования', 'error')
  }
}

const showNotification = (message, type = 'info') => {
  const event = new CustomEvent('notification', {
    detail: { message, type }
  })
  document.dispatchEvent(event)
}

const retryLastAction = async () => {
  if (!lastAction.value) return
  
  try {
    loadingResponse.value = true
    error.value = null
    
    switch (lastAction.value.type) {
      case 'send_message':
        await chatStore.sendMessage(lastAction.value.sessionId, lastAction.value.message)
        break
      case 'regenerate':
        await chatStore.regenerateLastResponse(lastAction.value.sessionId)
        break
      case 'edit_message':
        await chatStore.editMessage(lastAction.value.messageId, lastAction.value.newContent)
        break
      case 'delete_message':
        await chatStore.deleteMessage(lastAction.value.messageId)
        break
    }
    
    await nextTick()
    scrollToBottom(true)
  } catch (err) {
    console.error('Error retrying action:', err)
    error.value = 'Ошибка повтора действия: ' + (err.message || 'Попробуйте позже')
  } finally {
    loadingResponse.value = false
  }
}

const handleBack = () => {
  router.push('/')
}

const handleAttachment = () => {
  showNotification('Прикрепление файлов будет доступно в следующем обновлении', 'info')
}

const updateIsMobile = () => {
  isMobile.value = window.innerWidth < 768
}

// Хуки жизненного цикла
onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  try {
    loadingInitial.value = true
    await chatStore.loadSessions()
    
    // Если нет sessionId, создаем новую сессию
    if (!sessionId.value) {
      const newSession = await chatStore.createSession()
      sessionId.value = newSession.id
      router.replace({ name: 'chat-session', params: { sessionId: sessionId.value } })
    } else {
      // Загружаем сообщения для существующей сессии
      await chatStore.loadMessages(sessionId.value)
    }
    
  } catch (err) {
    console.error('Error initializing chat:', err)
    error.value = 'Ошибка инициализации чата: ' + (err.message || 'Попробуйте позже')
  } finally {
    loadingInitial.value = false
    scrollToBottom()
  }
  
  // Обновление времени каждую минуту
  const timeInterval = setInterval(() => {
    currentTime.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }, 60000)
  
  // Слушатель изменения размера окна
  window.addEventListener('resize', updateIsMobile)
  
  // Очистка при размонтировании
  onUnmounted(() => {
    clearInterval(timeInterval)
    window.removeEventListener('resize', updateIsMobile)
  })
})

watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

// Обновление высоты textarea при монтировании
watch(inputMessage, (newVal) => {
  nextTick(() => {
    const textarea = document.querySelector('.input-field')
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  })
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - var(--footer-height));
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 0 1rem;
}

.chat-header {
  background-color: var(--card-background);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
}

.chat-messages {
  background-color: var(--background-color);
  padding-bottom: 1rem;
  scroll-behavior: smooth;
}

.message-list-enter-active,
.message-list-leave-active {
  transition: all 0.3s ease;
}
.message-list-enter-from,
.message-list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.message-group {
  animation: fadeIn 0.3s ease-out;
}

.message {
  max-width: 85%;
  margin-bottom: 1rem;
  border-radius: var(--border-radius-medium);
  padding: 1rem;
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.message:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.message-user {
  background-color: var(--primary-color);
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.message-assistant {
  background-color: var(--card-background);
  color: var(--text-color);
  margin-right: auto;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px var(--shadow-color);
}

.message-error {
  background-color: var(--danger-color);
  color: white;
  margin-right: auto;
  border-bottom-left-radius: 4px;
}

.message-content {
  position: relative;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.message-sender {
  font-weight: 500;
}

.message-time {
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-left: auto;
}

.message-body {
  line-height: 1.6;
  word-wrap: break-word;
  font-size: 0.95rem;
}

.message-markdown {
  line-height: 1.8;
}

.message-markdown strong {
  font-weight: 600;
  color: var(--text-color);
}

.message-markdown em {
  font-style: italic;
  color: var(--text-secondary);
}

.message-markdown .inline-code {
  background-color: var(--border-color);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.message-link {
  color: var(--primary-color);
  text-decoration: underline;
  transition: color 0.2s ease;
}

.message-link:hover {
  color: #2980b9;
}

.message-footer {
  margin-top: 0.5rem;
  display: flex;
  justify-content: flex-end;
}

.message-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message:hover .message-actions {
  opacity: 1;
}

.message-action {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s ease, color 0.2s ease;
  font-size: 0.9rem;
}

.message-user .message-action {
  color: rgba(255, 255, 255, 0.8);
}

.message-user .message-action:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.message-assistant .message-action {
  color: var(--text-secondary);
}

.message-assistant .message-action:hover {
  background-color: var(--border-color);
  color: var(--text-color);
}

.message-assistant .message-action.active,
.message-assistant .message-action.active:hover {
  color: var(--primary-color);
}

.message-error .message-action {
  color: rgba(255, 255, 255, 0.9);
}

.message-error .message-action:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.copy-btn:hover {
  color: #3498db !important;
}

.edit-btn:hover {
  color: #f39c12 !important;
}

.delete-btn:hover {
  color: #e74c3c !important;
}

.like-btn:hover, .like-btn.active {
  color: #2ecc71 !important;
}

.dislike-btn:hover, .dislike-btn.active {
  color: #e74c3c !important;
}

.typing-indicator {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
  align-items: center;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: currentColor;
  border-radius: 50%;
  opacity: 0.4;
  animation: typing 1s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

.input-container {
  display: flex;
  gap: 0.5rem;
  background-color: var(--card-background);
  border-radius: var(--border-radius-large);
  padding: 0.5rem;
  box-shadow: 0 1px 3px var(--shadow-color);
  transition: box-shadow 0.2s ease;
}

.input-container:focus-within {
  box-shadow: 0 2px 6px rgba(52, 152, 219, 0.3);
}

.input-field {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-color);
  font-size: 1rem;
  resize: none;
  max-height: 200px;
  overflow-y: auto;
  padding: 0.75rem;
  min-height: 44px;
  line-height: 1.5;
}

.input-field:focus {
  outline: none;
}

.input-field::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.input-actions {
  display: flex;
  gap: 0.25rem;
}

.action-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease, color 0.2s ease;
}

.action-button:hover {
  background-color: var(--border-color);
  color: var(--text-color);
}

.send-button {
  background-color: var(--border-color);
  color: var(--text-secondary);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.send-button-active {
  background-color: var(--primary-color);
  color: white;
  transform: scale(1.05);
}

.send-button-active:hover {
  background-color: #2980b9;
  transform: scale(1.1);
}

.attachment-btn {
  display: none;
}

.char-counter {
  text-align: right;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.empty-state {
  color: var(--text-secondary);
}

.example-btn {
  transition: transform 0.2s ease;
}

.example-btn:hover {
  transform: translateY(-1px);
}

.back-button {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--border-radius-medium);
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
}

.back-button:hover {
  background-color: var(--border-color);
}

.session-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.retry-btn {
  margin-top: 0.5rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-5px); opacity: 1; }
}

@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - var(--header-height) - 60px);
  }
  
  .message {
    max-width: 95%;
  }
  
  .input-container {
    flex-direction: column;
  }
  
  .input-field {
    width: 100%;
    order: 1;
    min-height: 40px;
  }
  
  .input-actions {
    order: 2;
    width: 100%;
    justify-content: flex-end;
    padding: 0.25rem 0;
  }
  
  .send-button {
    width: 44px;
    height: 44px;
  }
  
  .attachment-btn {
    display: block;
  }
  
  .action-button span {
    display: none;
  }
  
  .hidden-mobile {
    display: none !important;
  }
  
  .session-title {
    max-width: 150px;
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 0.75rem;
  }
  
  .message-header {
    font-size: 0.8rem;
  }
  
  .input-field {
    font-size: 0.95rem;
  }
  
  .char-counter {
    font-size: 0.7rem;
  }
}
</style>