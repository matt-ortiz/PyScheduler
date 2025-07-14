<template>
  <div class="logs-view">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Execution Logs</h1>
      <div class="flex gap-2">
        <select 
          v-model="selectedScript" 
          @change="applyFilters"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800"
        >
          <option value="">All Scripts</option>
          <option v-for="script in scripts" :key="script.id" :value="script.id">
            {{ script.name }}
          </option>
        </select>
        <select 
          v-model="selectedStatus" 
          @change="applyFilters"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800"
        >
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="running">Running</option>
          <option value="timeout">Timeout</option>
        </select>
        <button 
          @click="refreshLogs"
          :disabled="loading"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {{ loading ? '🔄' : '🔄 Refresh' }}
        </button>
      </div>
    </div>

    <!-- Global Stats -->
    <div v-if="globalStats" class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div class="bg-blue-100 dark:bg-blue-900 p-4 rounded-lg text-center">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-300">{{ globalStats.total_executions }}</div>
        <div class="text-sm text-blue-800 dark:text-blue-200">Total Runs</div>
      </div>
      <div class="bg-green-100 dark:bg-green-900 p-4 rounded-lg text-center">
        <div class="text-2xl font-bold text-green-600 dark:text-green-300">{{ globalStats.successful_executions }}</div>
        <div class="text-sm text-green-800 dark:text-green-200">Successful</div>
      </div>
      <div class="bg-red-100 dark:bg-red-900 p-4 rounded-lg text-center">
        <div class="text-2xl font-bold text-red-600 dark:text-red-300">{{ globalStats.failed_executions }}</div>
        <div class="text-sm text-red-800 dark:text-red-200">Failed</div>
      </div>
      <div class="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-center">
        <div class="text-2xl font-bold text-gray-600 dark:text-gray-300">{{ Math.round(globalStats.success_rate) }}%</div>
        <div class="text-sm text-gray-800 dark:text-gray-200">Success Rate</div>
      </div>
      <div class="bg-purple-100 dark:bg-purple-900 p-4 rounded-lg text-center">
        <div class="text-2xl font-bold text-purple-600 dark:text-purple-300">{{ Math.round(globalStats.avg_duration_ms) }}ms</div>
        <div class="text-sm text-purple-800 dark:text-purple-200">Avg Duration</div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500">Loading execution logs...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="logs.length === 0" class="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div class="text-6xl mb-4">📋</div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No Execution Logs</h3>
      <p class="text-gray-500 dark:text-gray-400">
        {{ hasFilters ? 'No logs match your current filters.' : 'No scripts have been executed yet.' }}
      </p>
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
            <span class="font-medium text-gray-900 dark:text-gray-100">
              {{ getScriptName(log.script_id) }}
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
import { ref, computed, onMounted } from 'vue'
import { api } from '../composables/api'

export default {
  name: 'LogsView',
  setup() {
    const logs = ref([])
    const scripts = ref([])
    const globalStats = ref(null)
    const selectedLog = ref(null)
    const selectedScript = ref('')
    const selectedStatus = ref('')
    const loading = ref(false)
    const loadingMore = ref(false)
    const limit = 50
    const offset = ref(0)

    const hasFilters = computed(() => selectedScript.value || selectedStatus.value)

    async function loadScripts() {
      try {
        const response = await api.get('/api/scripts')
        scripts.value = response.data
      } catch (error) {
        console.error('Error loading scripts:', error)
      }
    }

    async function loadLogs(append = false) {
      if (!append) {
        loading.value = true
        offset.value = 0
      } else {
        loadingMore.value = true
      }

      try {
        const params = new URLSearchParams({
          limit: limit.toString(),
          offset: offset.value.toString()
        })

        if (selectedScript.value) {
          params.append('script_id', selectedScript.value)
        }
        
        if (selectedStatus.value) {
          params.append('status', selectedStatus.value)
        }

        const response = await api.get(`/api/logs?${params}`)
        
        if (append) {
          logs.value.push(...response.data)
        } else {
          logs.value = response.data
        }
        
        offset.value += limit
      } catch (error) {
        console.error('Error loading execution logs:', error)
      } finally {
        loading.value = false
        loadingMore.value = false
      }
    }

    async function loadGlobalStats() {
      try {
        const params = new URLSearchParams()
        
        if (selectedScript.value) {
          params.append('script_id', selectedScript.value)
        }

        const response = await api.get(`/api/logs/stats/summary?${params}`)
        globalStats.value = response.data
      } catch (error) {
        console.error('Error loading global stats:', error)
      }
    }

    async function refreshLogs() {
      await Promise.all([
        loadLogs(false),
        loadGlobalStats()
      ])
    }

    async function applyFilters() {
      selectedLog.value = null
      await refreshLogs()
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
          await loadGlobalStats()
        } catch (error) {
          console.error('Error deleting execution log:', error)
          alert('Failed to delete execution log')
        }
      }
    }

    function getScriptName(scriptId) {
      const script = scripts.value.find(s => s.id === scriptId)
      return script ? script.name : `Script ${scriptId}`
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

    function formatDateTime(dateString) {
      return new Date(dateString).toLocaleString()
    }

    function formatDuration(ms) {
      if (ms < 1000) return `${ms}ms`
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
      if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`
      return `${(ms / 3600000).toFixed(1)}h`
    }

    onMounted(async () => {
      await loadScripts()
      await refreshLogs()
    })

    return {
      logs,
      scripts,
      globalStats,
      selectedLog,
      selectedScript,
      selectedStatus,
      loading,
      loadingMore,
      hasFilters,
      limit,
      refreshLogs,
      applyFilters,
      loadMore,
      deleteLog,
      getScriptName,
      getStatusClass,
      formatDateTime,
      formatDuration
    }
  }
}
</script>

<style scoped>
.logs-view {
  max-width: 100%;
}

pre {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>