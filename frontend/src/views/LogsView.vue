<template>
  <div class="logs-view">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Execution Logs</h1>
      <div class="flex flex-wrap gap-2">
        <!-- Script Filter -->
        <select 
          v-model="selectedScript" 
          @change="applyFilters"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
        >
          <option value="">All Scripts</option>
          <option v-for="script in scripts" :key="script.id" :value="script.id">
            {{ script.name }}
          </option>
        </select>

        <!-- Status Filter -->
        <select 
          v-model="selectedStatus" 
          @change="applyFilters"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="running">Running</option>
          <option value="timeout">Timeout</option>
        </select>

        <!-- Date Range Filter -->
        <input 
          v-model="dateFrom" 
          @change="applyFilters"
          type="date" 
          placeholder="From date"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
        />
        <input 
          v-model="dateTo" 
          @change="applyFilters"
          type="date" 
          placeholder="To date"
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm"
        />

        <!-- Search Input -->
        <input 
          v-model="searchTerm" 
          @input="debounceSearch"
          type="text" 
          placeholder="Search logs..."
          class="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm flex-1 min-w-48"
        />

        <!-- Actions -->
        <div class="flex gap-2">
          <button 
            @click="refreshLogs"
            :disabled="loading"
            class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            {{ loading ? '🔄' : '🔄 Refresh' }}
          </button>
          
          <button 
            @click="clearFilters"
            v-if="hasFilters"
            class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
          >
            Clear Filters
          </button>

          <!-- Export Button -->
          <div class="relative">
            <button 
              @click="showExportMenu = !showExportMenu"
              class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
            >
              📊 Export
            </button>
            <div v-if="showExportMenu" class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border rounded shadow-lg z-10">
              <button 
                @click="exportLogs('csv')"
                class="block w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm"
              >
                Export as CSV
              </button>
              <button 
                @click="exportLogs('json')"
                class="block w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm"
              >
                Export as JSON
              </button>
            </div>
          </div>

          <!-- Bulk Actions -->
          <div class="relative" v-if="selectedLogs.length > 0">
            <button 
              @click="showBulkMenu = !showBulkMenu"
              class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
            >
              🗑️ Bulk ({{ selectedLogs.length }})
            </button>
            <div v-if="showBulkMenu" class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border rounded shadow-lg z-10">
              <button 
                @click="bulkDeleteLogs"
                class="block w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-red-600"
              >
                Delete Selected
              </button>
            </div>
          </div>

          <!-- Cleanup Button -->
          <button 
            @click="showCleanupDialog = true"
            class="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 text-sm"
          >
            🧹 Cleanup
          </button>
        </div>
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
        class="border rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
        :class="selectedLogs.includes(log.id) ? 'ring-2 ring-blue-500' : ''"
      >
        <!-- Log Header -->
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-3">
            <!-- Bulk Selection Checkbox -->
            <input 
              type="checkbox" 
              :checked="selectedLogs.includes(log.id)"
              @change="toggleLogSelection(log.id)"
              @click.stop
              class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            
            <span 
              class="px-2 py-1 text-xs rounded font-medium"
              :class="getStatusClass(log.status)"
            >
              {{ log.status.toUpperCase() }}
            </span>
            <span 
              class="font-medium text-gray-900 dark:text-gray-100 cursor-pointer"
              @click="selectedLog = selectedLog?.id === log.id ? null : log"
            >
              {{ getScriptName(log.script_id) }}
            </span>
            <span 
              class="text-sm text-gray-500 cursor-pointer"
              @click="selectedLog = selectedLog?.id === log.id ? null : log"
            >
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

    <!-- Cleanup Dialog -->
    <div v-if="showCleanupDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold mb-4">Cleanup Old Logs</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-4">
          Delete execution logs older than the specified number of days.
        </p>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Days to keep:</label>
          <input 
            v-model.number="cleanupDays" 
            type="number" 
            min="1" 
            max="365"
            class="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700"
          />
        </div>

        <div class="flex gap-2 justify-end">
          <button 
            @click="showCleanupDialog = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            Cancel
          </button>
          <button 
            @click="performCleanup"
            :disabled="cleanupLoading"
            class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            {{ cleanupLoading ? 'Cleaning...' : 'Cleanup' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../composables/api'
import { useAuthStore } from '../stores/auth'
import { useDateTime } from '../composables/datetime'

export default {
  name: 'LogsView',
  setup() {
    const authStore = useAuthStore()
    const { formatDateTime } = useDateTime()
    const logs = ref([])
    const scripts = ref([])
    const globalStats = ref(null)
    const selectedLog = ref(null)
    const selectedScript = ref('')
    const selectedStatus = ref('')
    const dateFrom = ref('')
    const dateTo = ref('')
    const searchTerm = ref('')
    const loading = ref(false)
    const loadingMore = ref(false)
    const limit = 50
    const offset = ref(0)
    
    // New state for enhanced features
    const selectedLogs = ref([])
    const showExportMenu = ref(false)
    const showBulkMenu = ref(false)
    const showCleanupDialog = ref(false)
    const cleanupDays = ref(30)
    const cleanupLoading = ref(false)
    const searchTimeout = ref(null)

    const hasFilters = computed(() => 
      selectedScript.value || selectedStatus.value || dateFrom.value || dateTo.value || searchTerm.value
    )

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

        if (dateFrom.value) {
          params.append('date_from', dateFrom.value)
        }

        if (dateTo.value) {
          params.append('date_to', dateTo.value)
        }

        if (searchTerm.value) {
          params.append('search', searchTerm.value)
        }

        const response = await api.get(`/api/logs/?${params}`)
        
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
      selectedLogs.value = []
      await refreshLogs()
    }

    async function loadMore() {
      await loadLogs(true)
    }

    function clearFilters() {
      selectedScript.value = ''
      selectedStatus.value = ''
      dateFrom.value = ''
      dateTo.value = ''
      searchTerm.value = ''
      selectedLog.value = null
      selectedLogs.value = []
      refreshLogs()
    }

    function debounceSearch() {
      if (searchTimeout.value) {
        clearTimeout(searchTimeout.value)
      }
      searchTimeout.value = setTimeout(() => {
        applyFilters()
      }, 500)
    }

    function toggleLogSelection(logId) {
      const index = selectedLogs.value.indexOf(logId)
      if (index > -1) {
        selectedLogs.value.splice(index, 1)
      } else {
        selectedLogs.value.push(logId)
      }
    }

    async function bulkDeleteLogs() {
      if (selectedLogs.value.length === 0) return
      
      const confirmMessage = `Are you sure you want to delete ${selectedLogs.value.length} execution logs?`
      if (!confirm(confirmMessage)) return

      try {
        await Promise.all(
          selectedLogs.value.map(logId => api.delete(`/api/logs/${logId}`))
        )
        
        logs.value = logs.value.filter(log => !selectedLogs.value.includes(log.id))
        selectedLogs.value = []
        showBulkMenu.value = false
        
        await loadGlobalStats()
        
        alert('Selected logs deleted successfully')
      } catch (error) {
        console.error('Error deleting logs:', error)
        alert('Failed to delete some logs')
      }
    }

    async function exportLogs(format) {
      showExportMenu.value = false
      
      try {
        const params = new URLSearchParams()
        if (selectedScript.value) params.append('script_id', selectedScript.value)
        if (selectedStatus.value) params.append('status', selectedStatus.value)
        if (dateFrom.value) params.append('date_from', dateFrom.value)
        if (dateTo.value) params.append('date_to', dateTo.value)
        if (searchTerm.value) params.append('search', searchTerm.value)
        
        // Get all logs for export (no pagination)
        params.append('limit', '10000')
        params.append('offset', '0')
        
        const response = await api.get(`/api/logs/?${params}`)
        const exportData = response.data
        
        let content
        let filename
        let mimeType
        
        if (format === 'csv') {
          content = convertToCSV(exportData)
          filename = `execution_logs_${new Date().toISOString().split('T')[0]}.csv`
          mimeType = 'text/csv'
        } else {
          content = JSON.stringify(exportData, null, 2)
          filename = `execution_logs_${new Date().toISOString().split('T')[0]}.json`
          mimeType = 'application/json'
        }
        
        const blob = new Blob([content], { type: mimeType })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        a.click()
        URL.revokeObjectURL(url)
        
      } catch (error) {
        console.error('Error exporting logs:', error)
        alert('Failed to export logs')
      }
    }

    function convertToCSV(data) {
      if (!data.length) return ''
      
      const headers = ['ID', 'Script ID', 'Status', 'Started At', 'Finished At', 'Duration (ms)', 'Exit Code', 'Triggered By']
      const rows = data.map(log => [
        log.id,
        log.script_id,
        log.status,
        log.started_at,
        log.finished_at || '',
        log.duration_ms || '',
        log.exit_code !== null ? log.exit_code : '',
        log.triggered_by || ''
      ])
      
      return [headers, ...rows].map(row => 
        row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
      ).join('\n')
    }

    async function performCleanup() {
      cleanupLoading.value = true
      
      try {
        const response = await api.post('/api/logs/cleanup', {
          days: cleanupDays.value
        })
        
        showCleanupDialog.value = false
        await refreshLogs()
        
        alert(response.data.message || 'Cleanup completed successfully')
      } catch (error) {
        console.error('Error cleaning up logs:', error)
        alert('Failed to cleanup logs')
      } finally {
        cleanupLoading.value = false
      }
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

    // Using shared datetime utility function

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
      dateFrom,
      dateTo,
      searchTerm,
      loading,
      loadingMore,
      hasFilters,
      limit,
      selectedLogs,
      showExportMenu,
      showBulkMenu,
      showCleanupDialog,
      cleanupDays,
      cleanupLoading,
      refreshLogs,
      applyFilters,
      loadMore,
      clearFilters,
      debounceSearch,
      toggleLogSelection,
      bulkDeleteLogs,
      exportLogs,
      performCleanup,
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