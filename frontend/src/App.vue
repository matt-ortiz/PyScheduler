<template>
  <div id="app" class="min-h-screen">
    <nav v-if="authStore.isAuthenticated" class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-primary-600 dark:text-primary-400">
              PyScheduler
            </router-link>
          </div>
          
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
              Scripts
            </router-link>
            <router-link to="/logs" class="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
              Logs
            </router-link>
            <router-link to="/settings" class="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
              Settings
            </router-link>
            
            <!-- User info and logout -->
            <div class="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
              <span>{{ authStore.user?.username }}</span>
              <button 
                @click="handleLogout"
                class="text-red-600 hover:text-red-500 dark:text-red-400 dark:hover:text-red-300"
              >
                Logout
              </button>
            </div>
            
            <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
              <svg v-if="!isDarkMode" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <router-view />
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const isDarkMode = ref(false)
    
    const toggleDarkMode = () => {
      isDarkMode.value = !isDarkMode.value
      if (isDarkMode.value) {
        document.documentElement.classList.add('dark')
        localStorage.setItem('darkMode', 'true')
      } else {
        document.documentElement.classList.remove('dark')
        localStorage.setItem('darkMode', 'false')
      }
    }
    
    const handleLogout = () => {
      authStore.logout()
      router.push('/login')
    }
    
    onMounted(() => {
      // Initialize auth store
      authStore.initializeAuth()
      
      // Initialize dark mode
      const savedDarkMode = localStorage.getItem('darkMode')
      if (savedDarkMode === 'true') {
        isDarkMode.value = true
        document.documentElement.classList.add('dark')
      }
    })
    
    return {
      authStore,
      isDarkMode,
      toggleDarkMode,
      handleLogout
    }
  }
}
</script>