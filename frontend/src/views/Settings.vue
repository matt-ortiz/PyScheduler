<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
    </div>

    <div class="space-y-6">
      <!-- System Information -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">System Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label">Application Version</label>
            <div class="text-sm text-gray-600 dark:text-gray-400">{{ version }}</div>
          </div>
          <div>
            <label class="label">Total Scripts</label>
            <div class="text-sm text-gray-600 dark:text-gray-400">{{ scripts.length }}</div>
          </div>
          <div>
            <label class="label">Total Executions</label>
            <div class="text-sm text-gray-600 dark:text-gray-400">{{ totalExecutions }}</div>
          </div>
          <div>
            <label class="label">Success Rate</label>
            <div class="text-sm text-gray-600 dark:text-gray-400">{{ successRate }}%</div>
          </div>
        </div>
      </div>

      <!-- Application Settings -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Application Settings</h2>
        <div class="space-y-4">
          <div>
            <label class="label">Theme</label>
            <select v-model="theme" @change="updateTheme" class="select">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>
          
          <div>
            <label class="label">Timezone</label>
            <select v-model="userTimezone" @change="updateTimezone" class="select">
              <option value="">Select timezone...</option>
              <option v-for="tz in timezones" :key="tz.value" :value="tz.value">
                {{ tz.label }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              Current time: {{ currentTime }} ({{ userTimezone }})
            </p>
            <p class="text-xs text-gray-400 mt-1">
              {{ timezones.length }} timezones loaded
            </p>
          </div>
          
          <div>
            <label class="label">Default Script Timeout (seconds)</label>
            <input v-model="settings.default_script_timeout" type="number" class="input">
          </div>
          
          <div>
            <label class="label">Default Memory Limit (MB)</label>
            <input v-model="settings.default_memory_limit" type="number" class="input">
          </div>
          
          <div>
            <label class="label">
              <input v-model="settings.rate_limit_enabled" type="checkbox" class="mr-2">
              Enable Rate Limiting
            </label>
          </div>
        </div>
      </div>

      <!-- Email Settings -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Email Settings</h2>
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="label">SMTP Server</label>
              <input v-model="emailSettings.smtp_server" type="text" class="input" placeholder="mail.smtp2go.com">
            </div>
            <div>
              <label class="label">SMTP Port</label>
              <input v-model="emailSettings.smtp_port" type="number" class="input" placeholder="2525">
            </div>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="label">Username</label>
              <input v-model="emailSettings.smtp_username" type="text" class="input">
            </div>
            <div>
              <label class="label">Password</label>
              <input v-model="emailSettings.smtp_password" type="password" class="input">
            </div>
          </div>
          
          <div>
            <label class="label">From Email</label>
            <input v-model="emailSettings.from_email" type="email" class="input" placeholder="pyscheduler@example.com">
          </div>
          
          <div class="flex space-x-2">
            <button @click="testEmailConnection" class="btn btn-primary">
              Test Connection
            </button>
            <button @click="saveEmailSettings" class="btn btn-secondary">
              Save Email Settings
            </button>
          </div>
        </div>
      </div>

      <!-- Database Management -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Database Management</h2>
        <div class="space-y-4">
          <div>
            <label class="label">Log Retention (days)</label>
            <input v-model="settings.log_retention_days" type="number" class="input">
          </div>
          
          <div>
            <label class="label">Max Logs per Script</label>
            <input v-model="settings.max_execution_logs" type="number" class="input">
          </div>
          
          <div class="flex space-x-2">
            <button @click="cleanupLogs" class="btn btn-danger">
              Clean Up Old Logs
            </button>
            <button @click="exportData" class="btn btn-secondary">
              Export Data
            </button>
          </div>
        </div>
      </div>

      <!-- API Settings -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">API Settings</h2>
        <div class="space-y-4">
          <div>
            <label class="label">API Key</label>
            <div class="flex space-x-2">
              <input v-model="settings.api_key" type="text" class="input font-mono" readonly>
              <button @click="copyApiKey" class="btn btn-secondary">
                Copy Key
              </button>
              <button @click="generateApiKey" class="btn btn-secondary">
                Generate New Key
              </button>
            </div>
          </div>
          
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <p>Use this API key to trigger scripts via URL:</p>
            <code class="bg-gray-100 dark:bg-gray-800 p-2 rounded block">
              GET /api/scripts/{safe_name}/trigger?api_key=YOUR_API_KEY
            </code>
            <p class="mt-2 text-xs">Replace {safe_name} with your script's safe name (e.g., "hello-world")</p>
          </div>
        </div>
      </div>

      <!-- Save Settings -->
      <div class="flex justify-end">
        <button @click="saveSettings" class="btn btn-primary">
          💾 Save All Settings
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useScriptStore } from '../stores/scripts'
import { useAuthStore } from '../stores/auth'
import { api } from '../composables/api'
import axios from 'axios'

export default {
  name: 'Settings',
  setup() {
    const scriptStore = useScriptStore()
    const authStore = useAuthStore()
    
    const theme = ref('dark')
    const userTimezone = ref('UTC')
    const version = ref('Loading...')
    const timezones = ref([
      { value: 'UTC', label: 'UTC' },
      { value: 'US/Eastern', label: 'Eastern Time' },
      { value: 'US/Central', label: 'Central Time' },
      { value: 'US/Mountain', label: 'Mountain Time' },
      { value: 'US/Pacific', label: 'Pacific Time' }
    ])
    const currentTime = ref('')
    const timeInterval = ref(null)
    const settings = ref({
      default_script_timeout: '300',
      default_memory_limit: '512',
      rate_limit_enabled: true,
      log_retention_days: '30',
      max_execution_logs: '1000',
      api_key: 'default-api-key-change-me'
    })
    
    const emailSettings = ref({
      smtp_server: '',
      smtp_port: '2525',
      smtp_username: '',
      smtp_password: '',
      from_email: ''
    })
    
    const scripts = computed(() => scriptStore.scripts)
    const totalExecutions = computed(() => {
      return scripts.value.reduce((sum, script) => sum + script.execution_count, 0)
    })
    const successRate = computed(() => {
      const total = totalExecutions.value
      const successful = scripts.value.reduce((sum, script) => sum + script.success_count, 0)
      return total > 0 ? Math.round((successful / total) * 100) : 0
    })
    
    const updateTheme = async () => {
      try {
        await authStore.updateUserSettings({ theme: theme.value })
        if (theme.value === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
        localStorage.setItem('theme', theme.value)
      } catch (error) {
        console.error('Error updating theme:', error)
        alert('Failed to update theme')
      }
    }
    
    const updateCurrentTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
        timeZone: userTimezone.value
      })
    }
    
    const updateTimezone = async () => {
      try {
        await authStore.updateUserSettings({ timezone: userTimezone.value })
        updateCurrentTime()
        alert('Timezone updated successfully!')
      } catch (error) {
        console.error('Error updating timezone:', error)
        alert('Failed to update timezone')
      }
    }
    
    const loadTimezones = async () => {
      try {
        const response = await axios.get('/api/auth/timezones')
        timezones.value = response.data
        console.log('Loaded timezones:', timezones.value)
      } catch (error) {
        console.error('Error loading timezones:', error)
        // Fallback to static timezones if API fails
        timezones.value = [
          { value: 'UTC', label: 'UTC' },
          { value: 'US/Eastern', label: 'Eastern Time' },
          { value: 'US/Central', label: 'Central Time' },
          { value: 'US/Mountain', label: 'Mountain Time' },
          { value: 'US/Pacific', label: 'Pacific Time' }
        ]
      }
    }
    
    const generateApiKey = async () => {
      try {
        const response = await axios.post('/api/settings/api-key/generate')
        settings.value.api_key = response.data.api_key
        alert('New API key generated successfully!')
      } catch (error) {
        alert(`Failed to generate API key: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const copyApiKey = async () => {
      try {
        await navigator.clipboard.writeText(settings.value.api_key)
        alert('API key copied to clipboard!')
      } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea')
        textArea.value = settings.value.api_key
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        alert('API key copied to clipboard!')
      }
    }
    
    const testEmailConnection = async () => {
      try {
        const response = await axios.post('/api/settings/email/test', emailSettings.value)
        if (response.data.success) {
          alert('Email connection test successful!')
        } else {
          alert(`Email connection test failed: ${response.data.error}`)
        }
      } catch (error) {
        alert(`Email connection test failed: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const saveEmailSettings = async () => {
      try {
        await axios.put('/api/settings/email', emailSettings.value)
        alert('Email settings saved successfully!')
      } catch (error) {
        alert(`Failed to save email settings: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const cleanupLogs = async () => {
      if (confirm('Are you sure you want to clean up old logs? This cannot be undone.')) {
        try {
          await axios.post('/api/logs/cleanup', { days: parseInt(settings.value.log_retention_days) })
          alert('Old logs cleaned up successfully')
        } catch (error) {
          alert('Failed to clean up logs')
        }
      }
    }
    
    const exportData = async () => {
      try {
        // This would export data from backend
        alert('Data export would be implemented here')
      } catch (error) {
        alert('Failed to export data')
      }
    }
    
    const saveSettings = async () => {
      try {
        const allSettings = {
          app_settings: settings.value,
          email_settings: emailSettings.value
        }
        await axios.put('/api/settings/', allSettings)
        alert('All settings saved successfully!')
      } catch (error) {
        alert(`Failed to save settings: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    onMounted(async () => {
      try {
        await scriptStore.fetchScripts()
        
        // Load theme from localStorage
        const savedTheme = localStorage.getItem('theme')
        if (savedTheme) {
          theme.value = savedTheme
        }
        
        // Load user timezone from auth store
        if (authStore.user && authStore.user.timezone) {
          userTimezone.value = authStore.user.timezone
        } else {
          userTimezone.value = 'UTC'
        }
        
        // Load version information
        try {
          const versionResponse = await axios.get('/api/version')
          version.value = versionResponse.data.version
        } catch (error) {
          console.error('Error loading version:', error)
          version.value = 'Error loading version'
        }
        
        // Load timezones and start time updates
        await loadTimezones()
        updateCurrentTime()
        timeInterval.value = setInterval(updateCurrentTime, 1000)
      } catch (error) {
        console.error('Error in onMounted:', error)
      }
      
      // Load settings from backend
      try {
        const response = await axios.get('/api/settings/')
        if (response.data.app_settings) {
          settings.value = response.data.app_settings
        }
        if (response.data.email_settings) {
          emailSettings.value = response.data.email_settings
        }
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    })
    
    onUnmounted(() => {
      if (timeInterval.value) {
        clearInterval(timeInterval.value)
      }
    })
    
    return {
      theme,
      userTimezone,
      timezones,
      currentTime,
      version,
      settings,
      emailSettings,
      scripts,
      totalExecutions,
      successRate,
      updateTheme,
      updateTimezone,
      generateApiKey,
      copyApiKey,
      testEmailConnection,
      saveEmailSettings,
      cleanupLogs,
      exportData,
      saveSettings
    }
  }
}
</script>