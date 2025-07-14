<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Execution Logs</h1>
      <button @click="refreshLogs" class="btn btn-secondary">
        🔄 Refresh
      </button>
    </div>

    <div class="card p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Filters</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="label">Script</label>
          <select v-model="filters.script_id" class="select">
            <option value="">All Scripts</option>
            <option v-for="script in scripts" :key="script.id" :value="script.id">
              {{ script.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="label">Status</label>
          <select v-model="filters.status" class="select">
            <option value="">All Status</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
          </select>
        </div>
        <div>
          <label class="label">Limit</label>
          <select v-model="filters.limit" class="select">
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p class="text-gray-500 mt-2">Loading logs...</p>
    </div>

    <div v-else-if="logs.length === 0" class="text-center py-12">
      <div class="text-gray-400 dark:text-gray-600 text-6xl mb-4">📝</div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No logs found</h3>
      <p class="text-gray-500 dark:text-gray-400">Execute some scripts to see logs here</p>
    </div>

    <div v-else class="space-y-4">
      <div v-for="log in logs" :key="log.id" class="card p-4">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-gray-100">
              {{ getScriptName(log.script_id) }}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Started: {{ formatDate(log.started_at) }}
              <span v-if="log.finished_at">
                • Finished: {{ formatDate(log.finished_at) }}
                • Duration: {{ formatDuration(log.duration_ms) }}
              </span>
            </p>
          </div>
          <div class="flex items-center space-x-2">
            <span :class="getStatusClass(log.status)">
              {{ log.status }}
            </span>
            <span v-if="log.exit_code !== null" class="text-sm text-gray-500">
              Exit: {{ log.exit_code }}
            </span>
          </div>
        </div>

        <div class="space-y-2">
          <div v-if="log.stdout" class="border-l-4 border-green-500 pl-4">
            <h4 class="text-sm font-medium text-green-700 dark:text-green-400 mb-1">Output</h4>
            <pre class="text-sm bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-x-auto">{{ log.stdout }}</pre>
          </div>
          
          <div v-if="log.stderr" class="border-l-4 border-red-500 pl-4">
            <h4 class="text-sm font-medium text-red-700 dark:text-red-400 mb-1">Error</h4>
            <pre class="text-sm bg-red-50 dark:bg-red-900 p-2 rounded overflow-x-auto">{{ log.stderr }}</pre>
          </div>
          
          <div v-if="!log.stdout && !log.stderr && log.status !== 'running'" class="text-sm text-gray-500 dark:text-gray-400 italic">
            No output
          </div>
          
          <div v-if="log.status === 'running'" class="text-sm text-blue-500 dark:text-blue-400 italic">
            Script is currently running...
          </div>
        </div>

        <div v-if="log.triggered_by" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            Triggered by: {{ log.triggered_by }}
          </span>
        </div>
      </div>
    </div>

    <!-- Load More Button -->
    <div v-if="logs.length >= filters.limit" class="text-center mt-6">
      <button @click="loadMore" class="btn btn-secondary">
        Load More
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useScriptStore } from '../stores/scripts'
import axios from 'axios'

export default {
  name: 'LogViewer',
  setup() {
    const scriptStore = useScriptStore()
    
    const logs = ref([])
    const loading = ref(false)
    const currentOffset = ref(0)
    
    const filters = ref({
      script_id: '',
      status: '',
      limit: '50'
    })
    
    const scripts = computed(() => scriptStore.scripts)
    
    const getScriptName = (scriptId) => {
      const script = scripts.value.find(s => s.id === scriptId)
      return script ? script.name : `Script ${scriptId}`
    }
    
    const getStatusClass = (status) => {
      switch (status) {
        case 'success':
          return 'status-badge status-success'
        case 'failed':
          return 'status-badge status-error'
        case 'running':
          return 'status-badge status-running'
        default:
          return 'status-badge status-pending'
      }
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }
    
    const formatDuration = (ms) => {
      if (ms < 1000) return `${ms}ms`
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
      return `${(ms / 60000).toFixed(1)}m`
    }
    
    const fetchLogs = async (reset = false) => {
      loading.value = true
      
      try {
        const params = new URLSearchParams()
        if (filters.value.script_id) params.append('script_id', filters.value.script_id)
        if (filters.value.status) params.append('status', filters.value.status)
        params.append('limit', filters.value.limit)
        if (!reset) params.append('offset', currentOffset.value)
        
        const response = await axios.get(`/api/logs?${params}`)
        
        if (reset) {
          logs.value = response.data
          currentOffset.value = 0
        } else {
          logs.value = [...logs.value, ...response.data]
        }
        
        currentOffset.value += response.data.length
      } catch (error) {
        console.error('Error fetching logs:', error)
        alert('Failed to fetch logs')
      } finally {
        loading.value = false
      }
    }
    
    const refreshLogs = () => {
      fetchLogs(true)
    }
    
    const loadMore = () => {
      fetchLogs(false)
    }
    
    // Watch for filter changes
    watch(filters, () => {
      fetchLogs(true)
    }, { deep: true })
    
    onMounted(async () => {
      await scriptStore.fetchScripts()
      await fetchLogs(true)
    })
    
    return {
      logs,
      loading,
      filters,
      scripts,
      getScriptName,
      getStatusClass,
      formatDate,
      formatDuration,
      refreshLogs,
      loadMore
    }
  }
}
</script>