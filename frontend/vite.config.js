import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ command, mode }) => {
  // Загружаем env переменные
  const env = loadEnv(mode, process.cwd(), '')
  
  // Безопасные настройки для продакшена
  const isProduction = mode === 'production'
  const apiBase = isProduction ? '/api/' : 'http://localhost:8050/api/'
  
  return {
    plugins: [vue()],
    base: isProduction ? './' : '/',
    server: {
      host: '0.0.0.0',
      port: 3001,
      strictPort: true,
      cors: {
        origin: ['http://localhost:3001', 'http://127.0.0.1:3001', 'http://147.45.184.36:3001'],
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        credentials: true
      },
      proxy: {
        '/api': {
          target: 'http://localhost:8050',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          secure: false,
          headers: {
            'X-Forwarded-Host': 'localhost:3001',
            'Origin': 'http://localhost:3001'
          }
        }
      }
    },
    build: {
      outDir: '../dist',
      assetsDir: 'assets',
      emptyOutDir: true,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              return 'vendor'
            }
          }
        }
      },
      sourcemap: !isProduction,
      minify: isProduction ? 'terser' : false,
      terserOptions: {
        compress: {
          drop_console: isProduction,
          drop_debugger: isProduction
        }
      }
    },
    preview: {
      port: 4173,
      strictPort: true
    },
    define: {
      __APP_ENV__: JSON.stringify({
        VITE_PRODUCTION: isProduction,
        VITE_API_BASE: apiBase,
        VITE_WS_BASE: isProduction ? 'wss://chat.mehhost.ru/ws/' : 'ws://localhost:8050/ws/'
      })
    }
  }
})