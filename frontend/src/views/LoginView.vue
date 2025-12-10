<template>
  <div class="auth-container flex flex-col items-center justify-center p-6">
    <div class="card w-full max-w-md">
      <div class="card-header text-center">
        <h2 class="text-2xl font-bold mb-2">Вход в систему</h2>
        <p class="text-secondary">Используйте ваши учетные данные для входа</p>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="username" class="form-label">Имя пользователя</label>
            <input 
              id="username" 
              v-model="username" 
              type="text" 
              class="form-control" 
              placeholder="Введите имя пользователя"
              required
            >
          </div>
          <div class="form-group">
            <label for="password" class="form-label">Пароль</label>
            <input 
              id="password" 
              v-model="password" 
              type="password" 
              class="form-control" 
              placeholder="Введите пароль"
              required
            >
          </div>
          <div class="form-group">
            <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
              <i class="material-icons" v-if="loading">hourglass_empty</i>
              <i class="material-icons" v-else>login</i>
              {{ loading ? 'Вход...' : 'Войти' }}
            </button>
          </div>
        </form>
      </div>
      <div class="card-footer text-center">
        <p>Нет аккаунта? 
          <router-link to="/register" class="text-primary hover:underline">Зарегистрироваться</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleSubmit = async () => {
  try {
    loading.value = true
    await authStore.login(username.value, password.value)
    
    const redirect = route.query.redirect || '/chat'
    router.push(redirect)
  } catch (error) {
    console.error('Login failed:', error)
    alert('Ошибка входа: ' + (error.message || 'Неверные учетные данные'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: 2rem;
}
.w-full {
  width: 100%;
}
.text-primary {
  color: var(--primary-color);
  cursor: pointer;
}
</style>
