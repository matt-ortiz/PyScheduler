<template>
  <div class="trigger-manager">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Script Triggers</h2>
      <button 
        @click="showAddTrigger = true"
        class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Add Trigger
      </button>
    </div>
    
    <!-- Existing triggers -->
    <div class="space-y-4 mb-6">
      <div v-if="triggers.length === 0" class="text-center py-8 text-gray-500">
        No triggers configured. Add a trigger to schedule this script.
      </div>
      
      <div 
        v-for="trigger in triggers" 
        :key="trigger.id"
        class="border rounded-lg p-4 bg-white dark:bg-gray-800"
      >
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-1 text-xs rounded" :class="triggerTypeClass(trigger.trigger_type)">
                {{ trigger.trigger_type.toUpperCase() }}
              </span>
              <span class="px-2 py-1 text-xs rounded" :class="trigger.enabled ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'">
                {{ trigger.enabled ? 'ENABLED' : 'DISABLED' }}
              </span>
            </div>
            
            <div class="text-sm text-gray-600 dark:text-gray-400 mb-1">
              {{ getTriggerDescription(trigger) }}
            </div>
            
            <div v-if="trigger.next_run_at" class="text-xs text-gray-500">
              Next run: {{ formatDateTime(trigger.next_run_at) }}
            </div>
          </div>
          
          <div class="flex gap-2">
            <button 
              @click="toggleTrigger(trigger)"
              class="px-3 py-1 text-sm rounded"
              :class="trigger.enabled ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : 'bg-green-100 text-green-800 hover:bg-green-200'"
            >
              {{ trigger.enabled ? 'Disable' : 'Enable' }}
            </button>
            <button 
              @click="editTrigger(trigger)"
              class="px-3 py-1 text-sm bg-blue-100 text-blue-800 hover:bg-blue-200 rounded"
            >
              Edit
            </button>
            <button 
              @click="deleteTrigger(trigger)"
              class="px-3 py-1 text-sm bg-red-100 text-red-800 hover:bg-red-200 rounded"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add/Edit trigger modal -->
    <div v-if="showAddTrigger || editingTrigger" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">
          {{ editingTrigger ? 'Edit Trigger' : 'Add New Trigger' }}
        </h3>
        
        <!-- Trigger type selection -->
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Trigger Type</label>
          <div class="grid grid-cols-4 gap-2">
            <button 
              v-for="type in triggerTypes" 
              :key="type.value"
              @click="selectedTriggerType = type.value"
              class="p-3 text-sm border rounded text-center"
              :class="selectedTriggerType === type.value ? 'bg-blue-500 text-white' : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'"
            >
              <div class="font-medium">{{ type.label }}</div>
              <div class="text-xs opacity-75">{{ type.description }}</div>
            </button>
          </div>
        </div>
        
        <!-- Scheduler components -->
        <div class="mb-4">
          <!-- Debug info -->
          <div class="p-3 bg-yellow-100 dark:bg-yellow-900 text-sm rounded mb-4">
            <strong>Debug Info:</strong><br>
            selectedTriggerType: {{ selectedTriggerType }}<br>
            scriptId: {{ scriptId }}<br>
            scriptSafeName: {{ scriptSafeName }}<br>
            Condition for Interval: {{ selectedTriggerType === 'interval' && scriptId }}
          </div>
          
          <CronBuilder 
            v-if="selectedTriggerType === 'cron' && scriptId"
            :script-id="scriptId"
            :initial-expression="editingTrigger?.config?.expression || '0 0 * * *'"
            @save="onTriggerSave"
            @cancel="closeModal"
          />
          
          <div v-if="selectedTriggerType === 'cron' && !scriptId" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
            <p class="text-sm text-gray-500">Loading script information...</p>
          </div>
          
          <IntervalScheduler 
            v-if="selectedTriggerType === 'interval' && scriptId"
            :script-safe-name="scriptSafeName"
            :initial-seconds="editingTrigger?.config?.seconds || 3600"
            @save="onTriggerSave"
            @cancel="closeModal"
          />
          
          <div v-if="selectedTriggerType === 'interval' && !scriptId" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
            <p class="text-sm text-gray-500">Loading script information...</p>
          </div>
          
          <!-- Additional debug for interval case -->
          <div v-if="selectedTriggerType === 'interval'" class="p-3 bg-blue-100 dark:bg-blue-900 text-sm rounded">
            <strong>Interval Debug:</strong><br>
            Should show IntervalScheduler: {{ scriptId ? 'YES' : 'NO' }}<br>
            Should show loading: {{ !scriptId ? 'YES' : 'NO' }}
          </div>
          
          <div v-if="selectedTriggerType === 'manual'" class="text-center py-8">
            <h4 class="text-lg font-medium mb-2">Manual Trigger</h4>
            <p class="text-gray-600 mb-4">This script will only run when manually executed.</p>
            <div class="flex gap-2 justify-center">
              <button 
                @click="createManualTrigger"
                :disabled="!scriptId"
                class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                Create Manual Trigger
              </button>
              <button 
                @click="closeModal"
                class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
          
          <div v-if="selectedTriggerType === 'startup'" class="text-center py-8">
            <h4 class="text-lg font-medium mb-2">Startup Trigger</h4>
            <p class="text-gray-600 mb-4">This script will run automatically when the system starts.</p>
            <div class="flex gap-2 justify-center">
              <button 
                @click="createStartupTrigger"
                :disabled="!scriptId"
                class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                Create Startup Trigger
              </button>
              <button 
                @click="closeModal"
                class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../composables/api'
import { useScriptStore } from '../stores/scripts'
import CronBuilder from './CronBuilder.vue'
import IntervalScheduler from './IntervalScheduler.vue'

export default {
  name: 'TriggerManager',
  components: {
    CronBuilder,
    IntervalScheduler
  },
  props: {
    scriptSafeName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const scriptStore = useScriptStore()
    const triggers = ref([])
    const showAddTrigger = ref(false)
    const editingTrigger = ref(null)
    const selectedTriggerType = ref('cron')
    
    // Get script ID from safe name
    const scriptId = computed(() => {
      const script = scriptStore.getScriptBySafeName(props.scriptSafeName)
      console.log('TriggerManager scriptId computed:', {
        scriptSafeName: props.scriptSafeName,
        script: script,
        scriptId: script ? script.id : null,
        allScripts: scriptStore.scripts.length
      })
      return script ? script.id : null
    })
    
    const triggerTypes = [
      { 
        value: 'cron', 
        label: 'CRON', 
        description: 'Schedule using CRON expressions' 
      },
      { 
        value: 'interval', 
        label: 'Interval', 
        description: 'Run at regular intervals' 
      },
      { 
        value: 'manual', 
        label: 'Manual', 
        description: 'Run only when triggered manually' 
      },
      { 
        value: 'startup', 
        label: 'Startup', 
        description: 'Run when system starts' 
      }
    ]
    
    async function loadTriggers() {
      try {
        if (!scriptId.value) {
          triggers.value = []
          return
        }
        const response = await api.get(`/api/execution/triggers?script_id=${scriptId.value}`)
        triggers.value = response.data
      } catch (error) {
        console.error('Error loading triggers:', error)
        // Show empty state if there's an error
        triggers.value = []
      }
    }
    
    function triggerTypeClass(type) {
      const classes = {
        cron: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        interval: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        manual: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
        startup: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
      }
      return classes[type] || 'bg-gray-100 text-gray-800'
    }
    
    function getTriggerDescription(trigger) {
      if (trigger.trigger_type === 'cron') {
        return `CRON: ${trigger.config.expression}`
      } else if (trigger.trigger_type === 'interval') {
        const seconds = trigger.config.seconds
        if (seconds < 60) return `Every ${seconds} seconds`
        if (seconds < 3600) return `Every ${Math.floor(seconds / 60)} minutes`
        if (seconds < 86400) return `Every ${Math.floor(seconds / 3600)} hours`
        return `Every ${Math.floor(seconds / 86400)} days`
      } else if (trigger.trigger_type === 'manual') {
        return 'Manual execution only'
      } else if (trigger.trigger_type === 'startup') {
        return 'Run on system startup'
      }
      return 'Unknown trigger type'
    }
    
    function formatDateTime(dateString) {
      return new Date(dateString).toLocaleString()
    }
    
    async function toggleTrigger(trigger) {
      try {
        await api.post(`/api/execution/triggers/${trigger.id}/toggle`)
        await loadTriggers()
      } catch (error) {
        console.error('Error toggling trigger:', error)
      }
    }
    
    function editTrigger(trigger) {
      editingTrigger.value = trigger
      selectedTriggerType.value = trigger.trigger_type
      showAddTrigger.value = true
    }
    
    async function deleteTrigger(trigger) {
      if (confirm('Are you sure you want to delete this trigger?')) {
        try {
          await api.delete(`/api/execution/triggers/${trigger.id}`)
          await loadTriggers()
        } catch (error) {
          console.error('Error deleting trigger:', error)
        }
      }
    }
    
    async function createManualTrigger() {
      if (!scriptId.value) {
        console.error('Cannot create manual trigger: script ID not available')
        return
      }
      
      try {
        console.log('Creating manual trigger for script ID:', scriptId.value)
        await api.post('/api/execution/triggers', {
          script_id: scriptId.value,
          trigger_type: 'manual',
          config: {},
          enabled: true
        })
        closeModal()
        await loadTriggers()
      } catch (error) {
        console.error('Error creating manual trigger:', error)
      }
    }
    
    async function createStartupTrigger() {
      if (!scriptId.value) {
        console.error('Cannot create startup trigger: script ID not available')
        return
      }
      
      try {
        console.log('Creating startup trigger for script ID:', scriptId.value)
        await api.post('/api/execution/triggers', {
          script_id: scriptId.value,
          trigger_type: 'startup',
          config: {},
          enabled: true
        })
        closeModal()
        await loadTriggers()
      } catch (error) {
        console.error('Error creating startup trigger:', error)
      }
    }
    
    function onTriggerSave(trigger) {
      closeModal()
      loadTriggers()
    }
    
    function closeModal() {
      showAddTrigger.value = false
      editingTrigger.value = null
      selectedTriggerType.value = 'cron'
    }
    
    onMounted(async () => {
      // Ensure scripts are loaded first
      console.log('TriggerManager onMounted - fetching scripts first')
      await scriptStore.fetchScripts()
      console.log('TriggerManager onMounted - scripts loaded, now loading triggers')
      loadTriggers()
    })
    
    return {
      triggers,
      showAddTrigger,
      editingTrigger,
      selectedTriggerType,
      triggerTypes,
      scriptId,
      scriptSafeName: props.scriptSafeName,
      loadTriggers,
      triggerTypeClass,
      getTriggerDescription,
      formatDateTime,
      toggleTrigger,
      editTrigger,
      deleteTrigger,
      createManualTrigger,
      createStartupTrigger,
      onTriggerSave,
      closeModal
    }
  }
}
</script>

<style scoped>
.trigger-manager {
  max-width: 1000px;
}
</style>