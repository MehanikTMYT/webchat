<template>
  <div class="not-found-container flex flex-col items-center justify-center text-center p-6">
    <h1 class="text-6xl font-bold mb-4">404</h1>
    <h2 class="text-2xl mb-6">Страница не найдена</h2>
    <p class="text-lg mb-8 max-w-md">
      К сожалению, запрашиваемая страница не существует или была перемещена.
    </p>
    <router-link to="/" class="btn btn-primary">
      <i class="material-icons">home</i> Вернуться на главную
    </router-link>
  </div>
</template>

<style scoped>
.not-found-container {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: 2rem;
}
</style>
