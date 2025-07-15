<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {{ isEditing ? 'Edit Script' : 'New Script' }}
      </h1>
      <div class="flex space-x-2">
        <button @click="executeScript" :disabled="!canExecute" class="btn btn-success">
          ▶ Run Script
        </button>
        <button @click="toggleEnabled" :class="script.enabled ? 'btn btn-warning' : 'btn btn-success'">
          {{ script.enabled ? '🔴 Disable' : '🟢 Enable' }}
        </button>
        <button @click="saveScript" class="btn btn-primary">
          💾 Save
        </button>
        <button v-if="isEditing" @click="deleteScript" class="btn btn-danger">
          🗑️ Delete
        </button>
        <button @click="goBack" class="btn btn-secondary">
          ← Back
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p class="text-gray-500 mt-2">Loading script...</p>
    </div>

    <div v-else class="space-y-6">
      <!-- Basic Information -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Basic Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label">Script Name</label>
            <input v-model="script.name" type="text" class="input" required>
          </div>
          <div>
            <label class="label">Folder</label>
            <select v-model="script.folder_id" class="select">
              <option value="">No folder</option>
              <option v-for="folder in folders" :key="folder.id" :value="folder.id">
                {{ folder.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="mt-4">
          <label class="label">Description</label>
          <textarea v-model="script.description" class="textarea" rows="2"></textarea>
        </div>
        
        <!-- API Trigger URL -->
        <div v-if="isEditing" class="mt-4">
          <label class="label">API Trigger URL</label>
          <div class="flex items-center space-x-2">
            <input 
              :value="apiTriggerUrl" 
              readonly 
              class="input flex-1 bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-400" 
              placeholder="API trigger URL will appear here"
            >
            <button @click="copyApiUrl" class="btn btn-secondary px-3">
              📋
            </button>
          </div>
          <p class="text-sm text-gray-500 mt-1">
            Use this URL to trigger the script remotely. API key is required.
          </p>
        </div>
      </div>

      <!-- Script Content -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Script Content</h2>
        <div>
          <label class="label">Python Code</label>
          <CodeEditor
            v-model="script.content"
            @change="onContentChange"
            language="python"
            placeholder="Enter your Python code here..."
            height="400px"
            max-height="600px"
            :dark-theme="isDarkMode"
          />
        </div>
      </div>

      <!-- Environment Settings -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Environment Settings</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Configuration Column -->
          <div class="space-y-4">
            <!-- Python Version -->
            <div>
              <label class="label">Python Version</label>
              <select v-model="script.python_version" class="select w-full">
                <option value="3.8">Python 3.8</option>
                <option value="3.9">Python 3.9</option>
                <option value="3.10">Python 3.10</option>
                <option value="3.11">Python 3.11</option>
                <option value="3.12">Python 3.12</option>
              </select>
            </div>
            
            <!-- Requirements -->
            <div>
              <label class="label">Requirements (pip packages)</label>
              <CodeEditor
                v-model="script.requirements"
                @change="onRequirementsChange"
                language="text"
                placeholder="requests==2.31.0&#10;numpy>=1.21.0&#10;pandas&#10;&#10;# Add one package per line&#10;# You can specify versions:&#10;# package==1.0.0 (exact)&#10;# package>=1.0.0 (minimum)&#10;# package~=1.0.0 (compatible)&#10;&#10;# Common packages:&#10;# requests - HTTP library&#10;# pandas - Data analysis&#10;# numpy - Numerical computing&#10;# matplotlib - Plotting&#10;# beautifulsoup4 - Web scraping"
                height="350px"
                max-height="450px"
                :dark-theme="isDarkMode"
              />
            </div>
          </div>
          
          <!-- Virtual Environment Status Column -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="label">Virtual Environment Status</label>
              <button @click="refreshVenvInfo" class="btn btn-sm btn-secondary" :disabled="venvLoading">
                {{ venvLoading ? '🔄' : '🔄 Refresh' }}
              </button>
            </div>
            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-600">
              <div v-if="venvLoading" class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
                <p class="text-sm text-gray-500">Loading environment info...</p>
              </div>
              
              <div v-else-if="venvInfo" class="space-y-4">
                <!-- Status Header -->
                <div class="border-b border-gray-200 dark:border-gray-600 pb-3">
                  <div class="flex items-center mb-2">
                    <span :class="venvInfo.venv_exists ? 'w-3 h-3 bg-green-500 rounded-full' : 'w-3 h-3 bg-red-500 rounded-full'" class="mr-2"></span>
                    <span class="text-sm font-medium">{{ venvInfo.message }}</span>
                  </div>
                  <div v-if="venvInfo.python_version" class="text-xs text-gray-600 dark:text-gray-400 font-mono">
                    {{ venvInfo.python_version }}
                  </div>
                  <div v-if="venvInfo.venv_path" class="text-xs text-gray-500 dark:text-gray-400 mt-1 break-all">
                    Path: {{ venvInfo.venv_path }}
                  </div>
                </div>
                
                <!-- Package List -->
                <div v-if="venvInfo.venv_exists && venvInfo.packages.length > 0">
                  <div class="flex justify-between items-center mb-2">
                    <h4 class="text-sm font-medium">Installed Packages</h4>
                    <span class="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                      {{ venvInfo.package_count }}
                    </span>
                  </div>
                  <div class="space-y-1">
                    <div v-for="pkg in venvInfo.packages" :key="pkg.name" 
                         class="text-xs bg-white dark:bg-gray-700 rounded px-2 py-1 flex justify-between items-center border border-gray-100 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-650">
                      <span class="font-mono font-medium">{{ pkg.name }}</span>
                      <span class="text-gray-500 dark:text-gray-400 text-right">{{ pkg.version }}</span>
                    </div>
                  </div>
                </div>
                
                <div v-else-if="venvInfo.venv_exists" class="text-center py-6 text-gray-500 dark:text-gray-400">
                  <div class="text-2xl mb-2">📦</div>
                  <p class="text-sm">No packages installed yet</p>
                  <p class="text-xs mt-1">Add requirements above and save to install packages</p>
                </div>
                
                <!-- Error Display -->
                <div v-if="venvInfo.error" class="p-3 bg-red-100 dark:bg-red-900 rounded text-sm border border-red-200 dark:border-red-700">
                  <div class="flex items-start">
                    <span class="text-red-500 mr-2">⚠️</span>
                    <div>
                      <strong class="text-red-800 dark:text-red-200">Error:</strong>
                      <div class="text-red-700 dark:text-red-300 mt-1">{{ venvInfo.error }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
                <div class="text-3xl mb-2">🐍</div>
                <p class="text-sm font-medium">Virtual Environment Info</p>
                <p class="text-xs mt-1">Save the script first to load environment details</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Execution Settings -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Execution Settings</h2>
        <div class="space-y-4">
          <div>
            <label class="label">
              <input v-model="script.email_notifications" type="checkbox" class="mr-2">
              Email Notifications
            </label>
          </div>
          <div v-if="script.email_notifications">
            <label class="label">Email Recipients (comma-separated)</label>
            <input v-model="script.email_recipients" type="text" class="input" 
                   placeholder="user@example.com, admin@example.com">
          </div>
          <div v-if="script.email_notifications">
            <label class="label">Email Trigger</label>
            <select v-model="script.email_trigger_type" class="select">
              <option value="all">Send on all executions</option>
              <option value="success">Send on success only</option>
              <option value="failure">Send on failure only</option>
            </select>
            <p class="text-sm text-gray-500 mt-1">
              Emails will include the complete console output (stdout and stderr).
            </p>
          </div>
          <div>
            <label class="label">Environment Variables (JSON)</label>
            <textarea 
              v-model="script.environment_variables" 
              class="textarea font-mono text-sm"
              rows="3"
              placeholder='{"API_KEY": "your-api-key", "DEBUG": "true"}'
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Scheduling -->
      <div v-if="isEditing && route.params.safeName" class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Script Scheduling</h2>
        <p class="text-sm text-gray-600 mb-4">Debug: Script Safe Name = {{ route.params.safeName }}, isEditing = {{ isEditing }}</p>
        <TriggerManager :script-safe-name="route.params.safeName" />
      </div>

      <!-- Execution History -->
      <div v-if="isEditing" class="card p-6">
        <div class="mb-4 text-sm text-gray-600">
          Debug: isEditing={{ isEditing }}, safeName={{ route.params.safeName }}
        </div>
        <ExecutionLogs :script-safe-name="route.params.safeName" />
      </div>
    </div>

    <!-- Execution Result Modal -->
    <div v-if="executionResult" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-4/5 max-w-4xl mx-4 max-h-4/5 overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold">Execution Result</h2>
          <button @click="executionResult = null" class="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>
        
        <div class="space-y-4">
          <div class="flex items-center space-x-4">
            <span :class="executionResult.success ? 'status-badge status-success' : 'status-badge status-error'">
              {{ executionResult.success ? 'Success' : 'Failed' }}
            </span>
            <span class="text-sm text-gray-500">
              Exit Code: {{ executionResult.exit_code }}
            </span>
            <span class="text-sm text-gray-500">
              Duration: {{ executionResult.duration_ms }}ms
            </span>
          </div>
          
          <div v-if="executionResult.stdout">
            <h3 class="font-semibold mb-2">Standard Output</h3>
            <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto">{{ executionResult.stdout }}</pre>
          </div>
          
          <div v-if="executionResult.stderr">
            <h3 class="font-semibold mb-2">Standard Error</h3>
            <pre class="bg-red-100 dark:bg-red-900 p-4 rounded-lg text-sm overflow-x-auto">{{ executionResult.stderr }}</pre>
          </div>
          
          <div v-if="executionResult.error">
            <h3 class="font-semibold mb-2">Error</h3>
            <pre class="bg-red-100 dark:bg-red-900 p-4 rounded-lg text-sm overflow-x-auto">{{ executionResult.error }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useScriptStore } from '../stores/scripts'
import TriggerManager from '../components/TriggerManager.vue'
import CodeEditor from '../components/CodeEditor.vue'
import ExecutionLogs from '../components/ExecutionLogs.vue'
import { api } from '../composables/api'

export default {
  name: 'ScriptEditor',
  components: {
    TriggerManager,
    CodeEditor,
    ExecutionLogs
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const scriptStore = useScriptStore()
    
    const loading = ref(false)
    const executionResult = ref(null)
    const autoSaveTimeout = ref(null)
    const venvInfo = ref(null)
    const venvLoading = ref(false)
    const requirementsTimeout = ref(null)
    
    const script = ref({
      name: '',
      description: '',
      content: 'print("Hello, World!")',
      folder_id: '',
      python_version: '3.12',
      requirements: '',
      enabled: true,
      email_notifications: false,
      email_recipients: '',
      email_trigger_type: 'all',
      environment_variables: '{}',
      execution_count: 0,
      success_count: 0,
      last_executed_at: null
    })
    
    const isEditing = computed(() => !!route.params.safeName)
    const folders = computed(() => scriptStore.folders)
    const canExecute = computed(() => script.value.name && script.value.content)
    const isDarkMode = computed(() => {
      // Check if user prefers dark mode
      return document.documentElement.classList.contains('dark') ||
             window.matchMedia('(prefers-color-scheme: dark)').matches
    })
    
    const apiTriggerUrl = computed(() => {
      if (!isEditing.value || !script.value.safe_name) return ''
      return `${window.location.origin}/api/scripts/${script.value.safe_name}/trigger?api_key=YOUR_API_KEY`
    })
    
    const onContentChange = () => {
      if (autoSaveTimeout.value) {
        clearTimeout(autoSaveTimeout.value)
      }
      
      if (isEditing.value) {
        autoSaveTimeout.value = setTimeout(() => {
          scriptStore.autoSaveScript(route.params.safeName, script.value.content)
        }, 1000)
      }
    }
    
    const onRequirementsChange = () => {
      if (requirementsTimeout.value) {
        clearTimeout(requirementsTimeout.value)
      }
      
      // Refresh venv info after requirements change (with delay)
      if (isEditing.value) {
        requirementsTimeout.value = setTimeout(() => {
          refreshVenvInfo()
        }, 2000)
      }
    }
    
    const toggleEnabled = () => {
      script.value.enabled = !script.value.enabled
    }
    
    const refreshVenvInfo = async () => {
      if (!isEditing.value) return
      
      venvLoading.value = true
      try {
        const response = await api.get(`/api/scripts/${route.params.safeName}/venv-info`)
        venvInfo.value = response.data
      } catch (error) {
        console.error('Error fetching venv info:', error)
        venvInfo.value = {
          venv_exists: false,
          packages: [],
          message: error.response?.data?.detail || 'Error loading environment info'
        }
      } finally {
        venvLoading.value = false
      }
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }
    
    const deleteScript = async () => {
      if (!isEditing.value) return
      
      const confirmed = confirm(`Are you sure you want to delete "${script.value.name}"? This action cannot be undone.`)
      if (!confirmed) return
      
      try {
        await scriptStore.deleteScript(route.params.safeName)
        alert('Script deleted successfully!')
        router.push({ name: 'ScriptList' })
      } catch (error) {
        alert(`Error deleting script: ${error.message}`)
      }
    }
    
    const copyApiUrl = async () => {
      if (!apiTriggerUrl.value) return
      
      try {
        await navigator.clipboard.writeText(apiTriggerUrl.value)
        alert('API trigger URL copied to clipboard!')
      } catch (error) {
        // Fallback for browsers that don't support clipboard API
        const textArea = document.createElement('textarea')
        textArea.value = apiTriggerUrl.value
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        alert('API trigger URL copied to clipboard!')
      }
    }
    
    const goBack = () => {
      router.push({ name: 'ScriptList' })
    }
    
    const saveScript = async () => {
      try {
        if (isEditing.value) {
          await scriptStore.updateScript(route.params.safeName, script.value)
        } else {
          const newScript = await scriptStore.createScript(script.value)
          router.push({ name: 'ScriptEditor', params: { safeName: newScript.safe_name } })
        }
        alert('Script saved successfully!')
      } catch (error) {
        alert(`Error saving script: ${error.message}`)
      }
    }
    
    const executeScript = async () => {
      try {
        if (isEditing.value) {
          executionResult.value = await scriptStore.executeScript(route.params.safeName)
        } else {
          alert('Please save the script first before executing')
        }
      } catch (error) {
        executionResult.value = {
          success: false,
          error: error.message,
          exit_code: -1,
          duration_ms: 0
        }
      }
    }
    
    onMounted(async () => {
      await scriptStore.fetchFolders()
      
      if (isEditing.value) {
        loading.value = true
        try {
          const fetchedScript = await scriptStore.fetchScript(route.params.safeName)
          script.value = { ...fetchedScript }
          
          // Load venv info after script is loaded
          setTimeout(() => {
            refreshVenvInfo()
          }, 500)
        } catch (error) {
          alert(`Error loading script: ${error.message}`)
          router.push({ name: 'ScriptList' })
        } finally {
          loading.value = false
        }
      }
    })
    
    return {
      script,
      loading,
      executionResult,
      isEditing,
      folders,
      canExecute,
      isDarkMode,
      venvInfo,
      venvLoading,
      apiTriggerUrl,
      onContentChange,
      onRequirementsChange,
      toggleEnabled,
      refreshVenvInfo,
      formatDate,
      deleteScript,
      copyApiUrl,
      goBack,
      saveScript,
      executeScript,
      route
    }
  }
}
</script>