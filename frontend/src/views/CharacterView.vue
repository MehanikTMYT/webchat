<template>
  <div class="characters-container">
    <div class="card">
      <div class="card-header">
        <h2 class="text-2xl font-bold flex items-center gap-2">
          <i class="material-icons">person</i>
          Персонажи
        </h2>
      </div>
      
      <div class="card-body">
        <div class="empty-state text-center py-12">
          <div class="text-4xl mb-4">🎭</div>
          <h3 class="text-xl font-semibold mb-2">Функция персонажей в разработке</h3>
          <p class="text-secondary mb-4">В будущих обновлениях вы сможете создавать и настраивать различных персонажей для общения</p>
          <button class="btn btn-primary" @click="showComingSoon">
            <i class="material-icons">info</i> Узнать больше
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const showComingSoon = () => {
  alert('Функция персонажей будет доступна в следующем обновлении. Следите за новостями!')
}
</script>

<style scoped>
.characters-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.empty-state {
  color: var(--text-secondary);
}
</style>
