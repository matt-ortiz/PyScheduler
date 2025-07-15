<template>
  <div class="execution-logs">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-semibold">Execution History</h3>
      <div class="text-xs text-gray-500">
        Debug: scriptSafeName={{ scriptSafeName }}, logs={{ logs.length }}, loading={{ loading }}
      </div>
      <div class="flex gap-2">
        <button 
          @click="refreshLogs"
          :disabled="loading"
          class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {{ loading ? '🔄' : '🔄 Refresh' }}
        </button>
        <button 
          @click="clearLogs"
          :disabled="loading || logs.length === 0"
          class="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
        >
          🗑️ Clear All
        </button>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="stats" class="grid grid-cols-4 gap-4 mb-4">
      <div class="bg-blue-100 dark:bg-blue-900 p-3 rounded">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-300">{{ stats.total_executions }}</div>
        <div class="text-sm text-blue-800 dark:text-blue-200">Total Runs</div>
      </div>
      <div class="bg-green-100 dark:bg-green-900 p-3 rounded">
        <div class="text-2xl font-bold text-green-600 dark:text-green-300">{{ stats.successful_executions }}</div>
        <div class="text-sm text-green-800 dark:text-green-200">Successful</div>
      </div>
      <div class="bg-red-100 dark:bg-red-900 p-3 rounded">
        <div class="text-2xl font-bold text-red-600 dark:text-red-300">{{ stats.failed_executions }}</div>
        <div class="text-sm text-red-800 dark:text-red-200">Failed</div>
      </div>
      <div class="bg-gray-100 dark:bg-gray-900 p-3 rounded">
        <div class="text-2xl font-bold text-gray-600 dark:text-gray-300">{{ Math.round(stats.success_rate) }}%</div>
        <div class="text-sm text-gray-800 dark:text-gray-200">Success Rate</div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500">Loading execution logs...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="logs.length === 0" class="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div class="text-6xl mb-4">📋</div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No Execution History</h3>
      <p class="text-gray-500 dark:text-gray-400">This script hasn't been executed yet.</p>
    </div>

    <!-- Logs List -->
    <div v-else class="space-y-3">
      <div 
        v-for="log in logs" 
        :key="log.id"
        class="border rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow cursor-pointer"
        @click="selectedLog = selectedLog?.id === log.id ? null : log"
      >
        <!-- Log Header -->
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-3">
            <span 
              class="px-2 py-1 text-xs rounded font-medium"
              :class="getStatusClass(log.status)"
            >
              {{ log.status.toUpperCase() }}
            </span>
            <span class="text-sm text-gray-500">
              {{ formatDateTime(log.started_at) }}
            </span>
            <span v-if="log.triggered_by" class="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              {{ log.triggered_by }}
            </span>
          </div>
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <span v-if="log.duration_ms">{{ formatDuration(log.duration_ms) }}</span>
            <span v-if="log.exit_code !== null">Exit: {{ log.exit_code }}</span>
            <button 
              @click.stop="deleteLog(log.id)"
              class="text-red-500 hover:text-red-700 text-xs px-2 py-1 rounded hover:bg-red-100 dark:hover:bg-red-900"
            >
              🗑️
            </button>
          </div>
        </div>

        <!-- Expandable Details -->
        <div v-if="selectedLog?.id === log.id" class="mt-4 space-y-3">
          <!-- Execution Details -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span class="font-medium">Started:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ formatDateTime(log.started_at) }}</div>
            </div>
            <div v-if="log.finished_at">
              <span class="font-medium">Finished:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ formatDateTime(log.finished_at) }}</div>
            </div>
            <div v-if="log.duration_ms">
              <span class="font-medium">Duration:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ formatDuration(log.duration_ms) }}</div>
            </div>
            <div v-if="log.exit_code !== null">
              <span class="font-medium">Exit Code:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ log.exit_code }}</div>
            </div>
          </div>

          <!-- Resource Usage -->
          <div v-if="log.max_memory_mb || log.max_cpu_percent" class="grid grid-cols-2 gap-4 text-sm">
            <div v-if="log.max_memory_mb">
              <span class="font-medium">Peak Memory:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ log.max_memory_mb }} MB</div>
            </div>
            <div v-if="log.max_cpu_percent">
              <span class="font-medium">Peak CPU:</span>
              <div class="text-gray-600 dark:text-gray-400">{{ log.max_cpu_percent.toFixed(1) }}%</div>
            </div>
          </div>

          <!-- Standard Output -->
          <div v-if="log.stdout">
            <h4 class="font-medium text-green-700 dark:text-green-400 mb-2">📤 Standard Output</h4>
            <pre class="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded p-3 text-sm overflow-x-auto whitespace-pre-wrap">{{ log.stdout }}</pre>
          </div>

          <!-- Standard Error -->
          <div v-if="log.stderr">
            <h4 class="font-medium text-red-700 dark:text-red-400 mb-2">❌ Standard Error</h4>
            <pre class="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded p-3 text-sm overflow-x-auto whitespace-pre-wrap">{{ log.stderr }}</pre>
          </div>

          <!-- No Output Message -->
          <div v-if="!log.stdout && !log.stderr" class="text-center py-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded">
            No output captured for this execution.
          </div>
        </div>

        <!-- Click hint -->
        <div v-if="!selectedLog || selectedLog.id !== log.id" class="text-xs text-gray-400 mt-2">
          Click to view details
        </div>
      </div>
    </div>

    <!-- Load More Button -->
    <div v-if="logs.length > 0 && logs.length >= limit" class="text-center mt-6">
      <button 
        @click="loadMore"
        :disabled="loadingMore"
        class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
      >
        {{ loadingMore ? 'Loading...' : 'Load More' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { api } from '../composables/api'
import { useDateTime } from '../composables/datetime'

export default {
  name: 'ExecutionLogs',
  props: {
    scriptSafeName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const { formatDateTime } = useDateTime()
    const logs = ref([])
    const stats = ref(null)
    const selectedLog = ref(null)
    const loading = ref(false)
    const loadingMore = ref(false)
    const limit = 20
    const offset = ref(0)

    async function loadLogs(append = false) {
      if (!append) {
        loading.value = true
        offset.value = 0
      } else {
        loadingMore.value = true
      }

      console.log('ExecutionLogs: Loading logs for script:', props.scriptSafeName)

      try {
        const url = `/api/logs/script/${props.scriptSafeName}?limit=${limit}&offset=${offset.value}`
        console.log('ExecutionLogs: Fetching from URL:', url)
        
        const response = await api.get(url)
        console.log('ExecutionLogs: Response received:', response.data)
        
        if (append) {
          logs.value.push(...response.data)
        } else {
          logs.value = response.data
        }
        
        offset.value += limit
        console.log('ExecutionLogs: Logs updated, count:', logs.value.length)
      } catch (error) {
        console.error('ExecutionLogs: Error loading execution logs:', error)
        console.error('ExecutionLogs: Error details:', error.response?.data)
      } finally {
        loading.value = false
        loadingMore.value = false
      }
    }

    async function loadStats() {
      try {
        // First get the script ID
        const scriptsResponse = await api.get('/api/scripts')
        const script = scriptsResponse.data.find(s => s.safe_name === props.scriptSafeName)
        
        if (script) {
          const response = await api.get(`/api/logs/stats/summary?script_id=${script.id}`)
          stats.value = response.data
        }
      } catch (error) {
        console.error('Error loading execution stats:', error)
      }
    }

    async function refreshLogs() {
      await Promise.all([
        loadLogs(false),
        loadStats()
      ])
    }

    async function loadMore() {
      await loadLogs(true)
    }

    async function deleteLog(logId) {
      if (confirm('Are you sure you want to delete this execution log?')) {
        try {
          await api.delete(`/api/logs/${logId}`)
          logs.value = logs.value.filter(log => log.id !== logId)
          
          // If we deleted the selected log, clear selection
          if (selectedLog.value?.id === logId) {
            selectedLog.value = null
          }
          
          // Refresh stats
          await loadStats()
        } catch (error) {
          console.error('Error deleting execution log:', error)
          alert('Failed to delete execution log')
        }
      }
    }

    async function clearLogs() {
      if (confirm('Are you sure you want to delete ALL execution logs for this script? This cannot be undone.')) {
        try {
          await api.delete(`/api/logs/script/${props.scriptSafeName}`)
          logs.value = []
          selectedLog.value = null
          stats.value = null
          await loadStats()
        } catch (error) {
          console.error('Error clearing execution logs:', error)
          alert('Failed to clear execution logs')
        }
      }
    }

    function getStatusClass(status) {
      const classes = {
        'success': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        'failed': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
        'running': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        'timeout': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      }
      return classes[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }

    // Using shared datetime utility function

    function formatDuration(ms) {
      if (ms < 1000) return `${ms}ms`
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
      if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`
      return `${(ms / 3600000).toFixed(1)}h`
    }

    // Watch for script changes
    watch(() => props.scriptSafeName, () => {
      selectedLog.value = null
      refreshLogs()
    })

    onMounted(() => {
      refreshLogs()
    })

    return {
      logs,
      stats,
      selectedLog,
      loading,
      loadingMore,
      limit,
      refreshLogs,
      loadMore,
      deleteLog,
      clearLogs,
      getStatusClass,
      formatDateTime,
      formatDuration
    }
  }
}
</script>

<style scoped>
.execution-logs {
  max-width: 100%;
}

pre {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>