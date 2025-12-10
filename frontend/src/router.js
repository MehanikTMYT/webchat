import { createRouter, createWebHistory } from 'vue-router'

// Импорт компонентов
const LoginView = () => import('./views/LoginView.vue')
const RegisterView = () => import('./views/RegisterView.vue')
const ChatView = () => import('./views/ChatView.vue')
const DashboardView = () => import('./views/DashboardView.vue')
const SettingsView = () => import('./views/SettingsView.vue')
const CharacterView = () => import('./views/CharacterView.vue')

export const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:sessionId',
    name: 'chat-session',
    component: ChatView,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/characters',
    name: 'characters',
    component: CharacterView,
    meta: { requiresAuth: true }
  },
  {
    path: '/characters/:characterId',
    name: 'character-detail',
    component: CharacterView,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { requiresGuest: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('./views/NotFoundView.vue')
  }
]

// Экспорт для использования в main.js
export default function() {
  return createRouter({
    history: createWebHistory(),
    routes
  })
}