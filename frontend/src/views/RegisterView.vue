<template>
  <div class="auth-container flex flex-col items-center justify-center p-6">
    <div class="card w-full max-w-md">
      <div class="card-header text-center">
        <h2 class="text-2xl font-bold mb-2">Регистрация</h2>
        <p class="text-secondary">Создайте новый аккаунт</p>
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
              placeholder="Выберите имя пользователя"
              required
              minlength="3"
              maxlength="30"
            >
          </div>
          <div class="form-group">
            <label for="password" class="form-label">Пароль</label>
            <input 
              id="password" 
              v-model="password" 
              type="password" 
              class="form-control" 
              placeholder="Создайте пароль"
              required
              minlength="6"
            >
          </div>
          <div class="form-group">
            <label for="confirmPassword" class="form-label">Подтвердите пароль</label>
            <input 
              id="confirmPassword" 
              v-model="confirmPassword" 
              type="password" 
              class="form-control" 
              placeholder="Повторите пароль"
              required
            >
          </div>
          <div class="form-group">
            <button type="submit" class="btn btn-secondary btn-lg w-full" :disabled="loading">
              <i class="material-icons" v-if="loading">hourglass_empty</i>
              <i class="material-icons" v-else>person_add</i>
              {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
            </button>
          </div>
        </form>
      </div>
      <div class="card-footer text-center">
        <p>Уже есть аккаунт? 
          <router-link to="/login" class="text-primary hover:underline">Войти</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const passwordMatch = computed(() => {
  return password.value === confirmPassword.value || confirmPassword.value === ''
})

const handleSubmit = async () => {
  if (!passwordMatch.value) {
    alert('Пароли не совпадают')
    return
  }

  try {
    loading.value = true
    await authStore.register(username.value, password.value)
    router.push('/chat')
  } catch (error) {
    console.error('Registration failed:', error)
    alert('Ошибка регистрации: ' + (error.message || 'Не удалось создать аккаунт'))
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
