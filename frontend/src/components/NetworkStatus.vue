<template>
  <div class="network-status">
    <span class="status-indicator online"></span>
    <span class="status-text">Онлайн</span>
  </div>
</template>

<style scoped>
.network-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.online {
  background-color: var(--success-color);
}
</style>
