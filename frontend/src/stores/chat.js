import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const messages = ref([])
  const loading = ref(false)
  
  const loadSessions = async () => {
    try {
      loading.value = true
      const response = await fetch('/api/sessions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Не удалось загрузить сессии')
      }
      
      const data = await response.json()
      sessions.value = data
      return data
    } catch (error) {
      console.error('Error loading sessions:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const createSession = async (title = 'Новый чат') => {
    try {
      loading.value = true
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        },
        body: JSON.stringify({ title })
      })
      
      if (!response.ok) {
        throw new Error('Не удалось создать сессию')
      }
      
      const session = await response.json()
      sessions.value.unshift(session)
      return session
    } catch (error) {
      console.error('Error creating session:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const loadMessages = async (sessionId) => {
    try {
      loading.value = true
      const response = await fetch(`/api/sessions/${sessionId}/messages`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Не удалось загрузить сообщения')
      }
      
      const data = await response.json()
      messages.value = [...messages.value, ...data.filter(m => !messages.value.some(existing => existing.id === m.id))]
      return data
    } catch (error) {
      console.error('Error loading messages:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const sendMessage = async (sessionId, message) => {
    try {
      loading.value = true
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        },
        body: JSON.stringify({ session_id: sessionId, message })
      })
      
      if (!response.ok) {
        throw new Error('Не удалось отправить сообщение')
      }
      
      const data = await response.json()
      
      // Добавляем сообщения в локальное состояние
      messages.value = [
        ...messages.value,
        { id: Date.now(), session_id: sessionId, role: 'user', content: message, created_at: new Date().toISOString() },
        { id: Date.now() + 1, session_id: sessionId, role: 'assistant', content: data.response, created_at: new Date().toISOString() }
      ]
      
      // Обновляем заголовок сессии, если он стандартный
      const session = sessions.value.find(s => s.id === sessionId)
      if (session && (session.title === 'Новый чат' || session.title === 'Untitled Chat')) {
        await updateSessionTitle(sessionId, `Чат: ${message.substring(0, 20)}${message.length > 20 ? '...' : ''}`)
      }
      
      return { userMessage: message, botResponse: data.response }
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const updateSessionTitle = async (sessionId, title) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        },
        body: JSON.stringify({ title })
      })
      
      if (!response.ok) {
        throw new Error('Не удалось обновить заголовок')
      }
      
      const updatedSession = await response.json()
      sessions.value = sessions.value.map(s => 
        s.id === sessionId ? updatedSession : s
      )
      
      return updatedSession
    } catch (error) {
      console.error('Error updating session title:', error)
      throw error
    }
  }
  
  const deleteSession = async (sessionId) => {
    try {
      loading.value = true
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Не удалось удалить сессию')
      }
      
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      messages.value = messages.value.filter(m => m.session_id !== sessionId)
      
      return true
    } catch (error) {
      console.error('Error deleting session:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const regenerateLastResponse = async (sessionId) => {
    try {
      loading.value = true
      
      // Находим последнее сообщение пользователя
      const sessionMessages = messages.value.filter(m => m.session_id === sessionId)
      const lastUserMessage = sessionMessages
        .filter(m => m.role === 'user')
        .slice(-1)[0]
      
      if (!lastUserMessage) {
        throw new Error('Нет сообщений для перегенерации')
      }
      
      // Удаляем последний ответ ассистента
      const lastAssistantMessage = sessionMessages
        .filter(m => m.role === 'assistant')
        .slice(-1)[0]
      
      if (lastAssistantMessage) {
        messages.value = messages.value.filter(m => m.id !== lastAssistantMessage.id)
      }
      
      // Отправляем то же сообщение заново
      const response = await fetch('/api/chat/regenerate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        },
        body: JSON.stringify({ 
          session_id: sessionId, 
          message_id: lastUserMessage.id 
        })
      })
      
      if (!response.ok) {
        throw new Error('Не удалось перегенерировать ответ')
      }
      
      const data = await response.json()
      
      // Добавляем новый ответ
      messages.value = [
        ...messages.value,
        { id: Date.now(), session_id: sessionId, role: 'assistant', content: data.response, created_at: new Date().toISOString() }
      ]
      
      return data.response
    } catch (error) {
      console.error('Error regenerating response:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const editMessage = async (messageId, newContent) => {
    try {
      loading.value = true
      
      // Находим сообщение
      const message = messages.value.find(m => m.id === messageId)
      if (!message || message.role !== 'user') {
        throw new Error('Нельзя редактировать это сообщение')
      }
      
      // Отправляем запрос на редактирование
      const response = await fetch(`/api/messages/${messageId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        },
        body: JSON.stringify({ content: newContent })
      })
      
      if (!response.ok) {
        throw new Error('Не удалось отредактировать сообщение')
      }
      
      // Обновляем сообщение в локальном состоянии
      messages.value = messages.value.map(m => 
        m.id === messageId ? { ...m, content: newContent } : m
      )
      
      return newContent
    } catch (error) {
      console.error('Error editing message:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const deleteMessage = async (messageId) => {
    try {
      loading.value = true
      
      const response = await fetch(`/api/messages/${messageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('chatbot_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Не удалось удалить сообщение')
      }
      
      // Удаляем сообщение и все последующие из локального состояния
      const messageIndex = messages.value.findIndex(m => m.id === messageId)
      if (messageIndex !== -1) {
        messages.value = messages.value.slice(0, messageIndex)
      }
      
      return true
    } catch (error) {
      console.error('Error deleting message:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  return {
    sessions,
    messages,
    loading,
    loadSessions,
    createSession,
    loadMessages,
    sendMessage,
    updateSessionTitle,
    deleteSession,
    regenerateLastResponse,
    editMessage,
    deleteMessage
  }
})
