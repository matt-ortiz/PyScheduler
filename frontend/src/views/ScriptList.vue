<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Scripts</h1>
      <button @click="showCreateDialog = true" class="btn btn-primary">
        + New Script
      </button>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p class="text-gray-500 mt-2">Loading scripts...</p>
    </div>

    <div v-else-if="error" class="card p-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
    </div>

    <div v-else class="space-y-4">
      <!-- Scripts without folders -->
      <div v-if="scriptsWithoutFolder.length > 0" class="space-y-3">
        <div v-for="script in scriptsWithoutFolder" :key="script.id" class="card p-4">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {{ script.name }}
              </h3>
              <p class="text-gray-600 dark:text-gray-400 text-sm mt-1">
                {{ script.description || 'No description' }}
              </p>
              <div class="flex items-center mt-2 space-x-4 text-sm text-gray-500 dark:text-gray-400">
                <span>Python {{ script.python_version }}</span>
                <span>{{ script.execution_count }} runs</span>
                <span v-if="script.last_executed_at">
                  Last run: {{ formatDate(script.last_executed_at) }}
                </span>
              </div>
              <div class="mt-2 text-xs text-gray-400">
                <span class="font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                  URL: /api/scripts/{{ script.safe_name }}/trigger?api_key=YOUR_API_KEY
                </span>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span :class="getStatusClass(script)">
                {{ script.enabled ? 'Enabled' : 'Disabled' }}
              </span>
              <button @click="executeScript(script.safe_name)" 
                      :disabled="!script.enabled"
                      class="btn btn-sm btn-primary">
                Run
              </button>
              <button @click="editScript(script.safe_name)" class="btn btn-sm btn-secondary">
                Edit
              </button>
              <button @click="deleteScript(script.safe_name, script.name)" class="btn btn-sm btn-danger">
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Folders with scripts -->
      <div v-for="folder in folders" :key="folder.id" class="card p-4">
        <div class="flex justify-between items-center mb-3">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
            📁 {{ folder.name }}
          </h2>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ getScriptsByFolder(folder.id).length }} scripts
          </span>
        </div>
        
        <div class="space-y-2">
          <div v-for="script in getScriptsByFolder(folder.id)" :key="script.id" 
               class="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <h3 class="font-medium text-gray-900 dark:text-gray-100">
                  {{ script.name }}
                </h3>
                <p class="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  {{ script.description || 'No description' }}
                </p>
                <div class="flex items-center mt-2 space-x-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>Python {{ script.python_version }}</span>
                  <span>{{ script.execution_count }} runs</span>
                  <span v-if="script.last_executed_at">
                    Last run: {{ formatDate(script.last_executed_at) }}
                  </span>
                </div>
                <div class="mt-2 text-xs text-gray-400">
                  <span class="font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                    URL: /api/scripts/{{ script.safe_name }}/trigger?api_key=YOUR_API_KEY
                  </span>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span :class="getStatusClass(script)">
                  {{ script.enabled ? 'Enabled' : 'Disabled' }}
                </span>
                <button @click="executeScript(script.safe_name)" 
                        :disabled="!script.enabled"
                        class="btn btn-sm btn-primary">
                  Run
                </button>
                <button @click="editScript(script.safe_name)" class="btn btn-sm btn-secondary">
                  Edit
                </button>
                <button @click="deleteScript(script.safe_name, script.name)" class="btn btn-sm btn-danger">
                  Delete
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
        <form @submit.prevent="createScript">
          <div class="mb-4">
            <label class="label">Script Name *</label>
            <input v-model="newScript.name" type="text" class="input" required placeholder="Enter script name">
          </div>
          
          <div class="flex justify-end space-x-2">
            <button type="button" @click="showCreateDialog = false" class="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary">
              Create Script
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

export default {
  name: 'ScriptList',
  setup() {
    const router = useRouter()
    const scriptStore = useScriptStore()
    
    const showCreateDialog = ref(false)
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
    const loading = computed(() => scriptStore.loading)
    const error = computed(() => scriptStore.error)
    
    const scriptsWithoutFolder = computed(() => scriptStore.getScriptsWithoutFolder)
    const getScriptsByFolder = (folderId) => scriptStore.getScriptsByFolder(folderId)
    
    const getStatusClass = (script) => {
      return script.enabled ? 'status-badge status-success' : 'status-badge status-pending'
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }
    
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
      try {
        const script = await scriptStore.createScript(newScript.value)
        showCreateDialog.value = false
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
        router.push({ name: 'ScriptEditor', params: { safeName: script.safe_name } })
      } catch (error) {
        alert(`Error creating script: ${error.message}`)
      }
    }
    
    onMounted(() => {
      scriptStore.fetchScripts()
      scriptStore.fetchFolders()
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
      getStatusClass,
      formatDate,
      editScript,
      executeScript,
      deleteScript,
      createScript
    }
  }
}
</script>