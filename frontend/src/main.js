import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

// Add version to console for debugging
console.log('🚀 PyScheduler Frontend')
console.log('📦 Build Date:', new Date().toISOString())
console.log('🔧 Check /api/version for backend version')

// Add version to window for easy access
window.PyScheduler = {
  buildDate: new Date().toISOString(),
  name: 'PyScheduler',
  repository: 'https://github.com/matt-ortiz/PyScheduler'
}