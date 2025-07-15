<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Scripts Dashboard</h1>
        <p class="text-gray-600 dark:text-gray-400 text-sm mt-1">Manage and monitor your Python scripts</p>
      </div>
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-4 text-sm">
          <div class="flex items-center space-x-1">
            <div class="w-2 h-2 bg-green-500 rounded-full"></div>
            <span class="text-gray-600 dark:text-gray-400">{{ enabledScripts }} enabled</span>
          </div>
          <div class="flex items-center space-x-1">
            <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span class="text-gray-600 dark:text-gray-400">{{ disabledScripts }} disabled</span>
          </div>
        </div>
        <button @click="showCreateDialog = true" class="btn btn-primary">
          + New Script
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p class="text-gray-500 mt-2">Loading scripts...</p>
    </div>

    <div v-else-if="error" class="card p-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
    </div>

    <div v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Total Scripts</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ scripts.length }}</p>
            </div>
            <div class="text-blue-500 text-2xl">📄</div>
          </div>
        </div>
        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Recent Runs</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ recentRuns }}</p>
            </div>
            <div class="text-blue-500 text-2xl">📊</div>
          </div>
        </div>
        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ successRate }}%</p>
            </div>
            <div class="text-green-500 text-2xl">✅</div>
          </div>
        </div>
        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Scheduled</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ scheduledScripts }}</p>
            </div>
            <div class="text-orange-500 text-2xl">⏰</div>
          </div>
        </div>
      </div>

      <!-- Scripts without folders -->
      <div v-if="scriptsWithoutFolder.length > 0" class="space-y-3">
        <div v-for="script in scriptsWithoutFolder" :key="script.id" class="card p-4 hover:shadow-md transition-shadow">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {{ script.name }}
                </h3>
                <span :class="getStatusClass(script)">
                  {{ script.enabled ? 'Enabled' : 'Disabled' }}
                </span>
                <span v-if="hasScheduledTriggers(script)" class="bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300 px-2 py-1 rounded-full text-xs">
                  Scheduled
                </span>
              </div>
              <p v-if="script.description" class="text-gray-600 dark:text-gray-400 text-sm mb-3">
                {{ script.description }}
              </p>
              <div class="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                <div class="flex items-center space-x-1">
                  <span class="text-orange-500">📅</span>
                  <span>{{ getScheduleInfo(script) }}</span>
                </div>
                <div v-if="getNextRunTime(script)" class="flex items-center space-x-1">
                  <span class="text-blue-500">⏰</span>
                  <span>Next: {{ formatDateTimeShort(getNextRunTime(script)) }}</span>
                </div>
                <div v-if="script.last_executed_at" class="flex items-center space-x-1">
                  <span class="text-gray-500">⏱️</span>
                  <span>Last: {{ formatDateTimeShort(script.last_executed_at) }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button @click="executeScript(script.safe_name)" 
                      :disabled="!script.enabled"
                      class="btn btn-sm btn-primary"
                      :class="{ 'opacity-50 cursor-not-allowed': !script.enabled }">
                ▶️ Run
              </button>
              <button @click="editScript(script.safe_name)" class="btn btn-sm btn-secondary">
                ✏️ Edit
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Folders with scripts -->
      <div v-for="folder in folders" :key="folder.id" class="card p-4 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-center mb-3">
          <div class="flex items-center space-x-3">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
              📁 {{ folder.name }}
            </h2>
            <span class="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 px-2 py-1 rounded-full text-xs">
              {{ getScriptsByFolder(folder.id).length }} scripts
            </span>
          </div>
          <button @click="toggleFolder(folder.id)" class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            <span v-if="expandedFolders.includes(folder.id)">▼</span>
            <span v-else>▶</span>
          </button>
        </div>
        
        <div v-show="expandedFolders.includes(folder.id)" class="space-y-2">
          <div v-for="script in getScriptsByFolder(folder.id)" :key="script.id" 
               class="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                  <h3 class="font-medium text-gray-900 dark:text-gray-100">
                    {{ script.name }}
                  </h3>
                  <span :class="getStatusClass(script)">
                    {{ script.enabled ? 'Enabled' : 'Disabled' }}
                  </span>
                  <span v-if="hasScheduledTriggers(script)" class="bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300 px-2 py-1 rounded-full text-xs">
                    Scheduled
                  </span>
                </div>
                <p v-if="script.description" class="text-gray-600 dark:text-gray-400 text-sm mb-3">
                  {{ script.description }}
                </p>
                <div class="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                  <div class="flex items-center space-x-1">
                    <span class="text-orange-500">📅</span>
                    <span>{{ getScheduleInfo(script) }}</span>
                  </div>
                  <div v-if="getNextRunTime(script)" class="flex items-center space-x-1">
                    <span class="text-blue-500">⏰</span>
                    <span>Next: {{ formatDateTimeShort(getNextRunTime(script)) }}</span>
                  </div>
                  <div v-if="script.last_executed_at" class="flex items-center space-x-1">
                    <span class="text-gray-500">⏱️</span>
                    <span>Last: {{ formatDateTimeShort(script.last_executed_at) }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <button @click="executeScript(script.safe_name)" 
                        :disabled="!script.enabled"
                        class="btn btn-sm btn-primary"
                        :class="{ 'opacity-50 cursor-not-allowed': !script.enabled }">
                  ▶️ Run
                </button>
                <button @click="editScript(script.safe_name)" class="btn btn-sm btn-secondary">
                  ✏️ Edit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="scripts.length === 0" class="text-center py-12">
        <div class="text-gray-400 dark:text-gray-600 text-6xl mb-4">📄</div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No scripts yet</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">Create your first script to get started</p>
        <button @click="showCreateDialog = true" class="btn btn-primary">
          Create Script
        </button>
      </div>
    </div>

    <!-- Create Script Dialog -->
    <div v-if="showCreateDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-[400px] max-w-full mx-4">
        <h2 class="text-xl font-bold mb-4">Create New Script</h2>
        
        <!-- Loading State -->
        <div v-if="isCreating" class="text-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <h3 class="text-lg font-semibold mb-2">Creating Script...</h3>
          <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <div class="flex items-center justify-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full" v-if="creationStep >= 1"></div>
              <div class="w-2 h-2 bg-gray-300 rounded-full animate-pulse" v-else></div>
              <span>Validating script name...</span>
            </div>
            <div class="flex items-center justify-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full" v-if="creationStep >= 2"></div>
              <div class="w-2 h-2 bg-gray-300 rounded-full animate-pulse" v-else></div>
              <span>Creating database record...</span>
            </div>
            <div class="flex items-center justify-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full" v-if="creationStep >= 3"></div>
              <div class="w-2 h-2 bg-gray-300 rounded-full animate-pulse" v-else></div>
              <span>Setting up virtual environment...</span>
            </div>
            <div class="flex items-center justify-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full" v-if="creationStep >= 4"></div>
              <div class="w-2 h-2 bg-gray-300 rounded-full animate-pulse" v-else></div>
              <span>Finalizing setup...</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-4">This may take a few seconds...</p>
        </div>

        <!-- Creation Form -->
        <form v-else @submit.prevent="createScript">
          <div class="mb-4">
            <label class="label">Script Name *</label>
            <input 
              v-model="newScript.name" 
              type="text" 
              class="input" 
              required 
              placeholder="Enter script name"
              :disabled="isCreating"
            >
          </div>
          
          <!-- Error Message -->
          <div v-if="createError" class="mb-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-600 rounded text-red-700 dark:text-red-400 text-sm">
            {{ createError }}
          </div>
          
          <div class="flex justify-end space-x-2">
            <button 
              type="button" 
              @click="cancelCreate" 
              class="btn btn-secondary"
              :disabled="isCreating"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="isCreating || !newScript.name.trim()"
            >
              <span v-if="isCreating" class="flex items-center">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating...
              </span>
              <span v-else>Create Script</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScriptStore } from '../stores/scripts'
import { useAuthStore } from '../stores/auth'
import { useDateTime } from '../composables/datetime'

export default {
  name: 'ScriptList',
  setup() {
    const router = useRouter()
    const scriptStore = useScriptStore()
    const authStore = useAuthStore()
    const { formatDateTimeShort, formatDate } = useDateTime()
    
    const showCreateDialog = ref(false)
    const isCreating = ref(false)
    const creationStep = ref(0)
    const createError = ref('')
    const expandedFolders = ref([])
    const newScript = ref({
      name: '',
      description: '',
      folder_id: null,
      content: 'print("Hello, World!")',
      python_version: '3.12',
      requirements: '',
      email_notifications: false,
      email_recipients: '',
      environment_variables: '{}',
      auto_save: true
    })
    
    const scripts = computed(() => scriptStore.scripts)
    const folders = computed(() => scriptStore.folders)
    const triggers = computed(() => scriptStore.triggers)
    const loading = computed(() => scriptStore.loading)
    const error = computed(() => scriptStore.error)
    
    const scriptsWithoutFolder = computed(() => scriptStore.getScriptsWithoutFolder)
    const getScriptsByFolder = (folderId) => scriptStore.getScriptsByFolder(folderId)
    
    // Dashboard summary computed values
    const enabledScripts = computed(() => scripts.value.filter(script => script.enabled).length)
    const disabledScripts = computed(() => scripts.value.filter(script => !script.enabled).length)
    const recentRuns = computed(() => {
      const today = new Date()
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      return scripts.value.filter(script => 
        script.last_executed_at && new Date(script.last_executed_at) >= yesterday
      ).length
    })
    const successRate = computed(() => {
      const total = scripts.value.reduce((sum, script) => sum + script.execution_count, 0)
      const successful = scripts.value.reduce((sum, script) => sum + script.success_count, 0)
      return total > 0 ? Math.round((successful / total) * 100) : 0
    })
    const scheduledScripts = computed(() => {
      // This would need to be implemented based on triggers data
      return scripts.value.filter(script => script.enabled && hasScheduledTriggers(script)).length
    })
    
    const getStatusClass = (script) => {
      return script.enabled ? 'status-badge status-success' : 'status-badge status-pending'
    }
    
    const hasScheduledTriggers = (script) => {
      const scriptTriggers = scriptStore.getTriggersByScript(script.id)
      return scriptTriggers.some(trigger => trigger.enabled && trigger.trigger_type !== 'manual')
    }
    
    const getScheduleInfo = (script) => {
      const scriptTriggers = scriptStore.getTriggersByScript(script.id)
      const enabledTriggers = scriptTriggers.filter(trigger => trigger.enabled)
      
      if (enabledTriggers.length === 0) {
        return 'Manual only'
      }
      
      // Find the first enabled scheduled trigger (not manual)
      const scheduledTrigger = enabledTriggers.find(trigger => trigger.trigger_type !== 'manual')
      
      if (!scheduledTrigger) {
        return 'Manual only'
      }
      
      return formatScheduleType(scheduledTrigger)
    }
    
    const formatScheduleType = (trigger) => {
      switch (trigger.trigger_type) {
        case 'cron':
          return formatCronExpression(trigger.config.expression)
        case 'interval':
          return formatIntervalConfig(trigger.config)
        case 'startup':
          return 'On system startup'
        case 'manual':
          return 'Manual only'
        default:
          return 'Unknown schedule'
      }
    }
    
    const formatCronExpression = (expression) => {
      // Convert common CRON expressions to human-readable format
      const patterns = {
        '0 * * * *': 'Every hour',
        '0 */2 * * *': 'Every 2 hours',
        '0 */3 * * *': 'Every 3 hours',
        '0 */6 * * *': 'Every 6 hours',
        '0 */12 * * *': 'Every 12 hours',
        '0 0 * * *': 'Daily at midnight',
        '0 9 * * *': 'Daily at 9:00 AM',
        '0 12 * * *': 'Daily at noon',
        '0 18 * * *': 'Daily at 6:00 PM',
        '0 0 * * 0': 'Weekly on Sunday',
        '0 0 1 * *': 'Monthly on 1st',
        '*/5 * * * *': 'Every 5 minutes',
        '*/10 * * * *': 'Every 10 minutes',
        '*/15 * * * *': 'Every 15 minutes',
        '*/30 * * * *': 'Every 30 minutes'
      }
      
      return patterns[expression] || `Custom: ${expression}`
    }
    
    const formatIntervalConfig = (config) => {
      const seconds = config.seconds || 0
      
      if (seconds < 60) {
        return `Every ${seconds} seconds`
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60)
        return `Every ${minutes} minute${minutes > 1 ? 's' : ''}`
      } else if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600)
        return `Every ${hours} hour${hours > 1 ? 's' : ''}`
      } else {
        const days = Math.floor(seconds / 86400)
        return `Every ${days} day${days > 1 ? 's' : ''}`
      }
    }
    
    const getNextRunTime = (script) => {
      const scriptTriggers = scriptStore.getTriggersByScript(script.id)
      const enabledTriggers = scriptTriggers.filter(trigger => trigger.enabled && trigger.next_run_at)
      
      if (enabledTriggers.length === 0) {
        return null
      }
      
      // Find the trigger with the earliest next run time
      const earliestTrigger = enabledTriggers.reduce((earliest, trigger) => {
        if (!earliest || new Date(trigger.next_run_at) < new Date(earliest.next_run_at)) {
          return trigger
        }
        return earliest
      }, null)
      
      return earliestTrigger ? earliestTrigger.next_run_at : null
    }
    
    const toggleFolder = (folderId) => {
      const index = expandedFolders.value.indexOf(folderId)
      if (index > -1) {
        expandedFolders.value.splice(index, 1)
      } else {
        expandedFolders.value.push(folderId)
      }
    }
    
    // Using shared datetime utility functions
    
    const editScript = (safeName) => {
      router.push({ name: 'ScriptEditor', params: { safeName: safeName } })
    }
    
    const executeScript = async (safeName) => {
      try {
        await scriptStore.executeScript(safeName)
        // Refresh scripts to update execution count
        await scriptStore.fetchScripts()
      } catch (error) {
        alert(`Error executing script: ${error.message}`)
      }
    }

    const deleteScript = async (safeName, scriptName) => {
      if (confirm(`Are you sure you want to delete the script "${scriptName}"? This action cannot be undone.`)) {
        try {
          await scriptStore.deleteScript(safeName)
          // Refresh scripts list after deletion
          await scriptStore.fetchScripts()
        } catch (error) {
          alert(`Error deleting script: ${error.message}`)
        }
      }
    }
    
    const createScript = async () => {
      if (isCreating.value) return // Prevent duplicate submissions
      
      isCreating.value = true
      createError.value = ''
      creationStep.value = 0
      
      try {
        // Step 1: Validating script name
        creationStep.value = 1
        await new Promise(resolve => setTimeout(resolve, 300)) // Brief pause for UX
        
        // Step 2: Creating database record  
        creationStep.value = 2
        await new Promise(resolve => setTimeout(resolve, 200))
        
        // Step 3: Setting up virtual environment (this is the actual API call)
        creationStep.value = 3
        const script = await scriptStore.createScript(newScript.value)
        
        // Step 4: Finalizing setup
        creationStep.value = 4
        await new Promise(resolve => setTimeout(resolve, 200))
        
        // Success - reset form and navigate
        showCreateDialog.value = false
        resetForm()
        router.push({ name: 'ScriptEditor', params: { safeName: script.safe_name } })
        
      } catch (error) {
        createError.value = error.message || 'Failed to create script'
      } finally {
        isCreating.value = false
        creationStep.value = 0
      }
    }
    
    const resetForm = () => {
      newScript.value = {
        name: '',
        description: '',
        folder_id: null,
        content: 'print("Hello, World!")',
        python_version: '3.12',
        requirements: '',
        email_notifications: false,
        email_recipients: '',
        environment_variables: '{}',
        auto_save: true
      }
      createError.value = ''
    }
    
    const cancelCreate = () => {
      if (isCreating.value) return // Don't allow cancel during creation
      showCreateDialog.value = false
      resetForm()
    }
    
    onMounted(async () => {
      await scriptStore.fetchScripts()
      await scriptStore.fetchFolders()
      await scriptStore.fetchTriggers()
      // Expand all folders by default
      setTimeout(() => {
        expandedFolders.value = folders.value.map(folder => folder.id)
      }, 100)
    })
    
    return {
      scripts,
      folders,
      loading,
      error,
      scriptsWithoutFolder,
      getScriptsByFolder,
      showCreateDialog,
      newScript,
      isCreating,
      creationStep,
      createError,
      expandedFolders,
      enabledScripts,
      disabledScripts,
      recentRuns,
      successRate,
      scheduledScripts,
      getStatusClass,
      hasScheduledTriggers,
      getScheduleInfo,
      getNextRunTime,
      toggleFolder,
      formatDate,
      formatDateTimeShort,
      editScript,
      executeScript,
      deleteScript,
      createScript,
      cancelCreate
    }
  }
}
</script>