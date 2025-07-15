<template>
  <div class="interval-scheduler">
    <h3 class="text-lg font-semibold mb-4">Interval Scheduler</h3>
    
    <div class="mb-4">
      <h4 class="text-sm font-medium mb-2">Quick Presets</h4>
      <div class="flex flex-wrap gap-2">
        <button 
          v-for="preset in presets" 
          :key="preset.label"
          @click="applyPreset(preset)"
          class="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 rounded"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>
    
    <div class="grid grid-cols-3 gap-4 mb-4">
      <div>
        <label class="block text-sm font-medium mb-1">Value</label>
        <input 
          v-model.number="interval.value"
          type="number"
          min="1"
          class="w-full p-2 border rounded dark:bg-gray-800"
          placeholder="1"
        />
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Unit</label>
        <select 
          v-model="interval.unit"
          class="w-full p-2 border rounded dark:bg-gray-800"
        >
          <option value="seconds">Seconds</option>
          <option value="minutes">Minutes</option>
          <option value="hours">Hours</option>
          <option value="days">Days</option>
        </select>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Total Seconds</label>
        <input 
          :value="totalSeconds"
          readonly
          class="w-full p-2 border rounded dark:bg-gray-800 bg-gray-50 dark:bg-gray-700"
        />
      </div>
    </div>
    
    <div class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded">
      <p class="text-sm">
        <strong>Description:</strong> {{ intervalDescription }}
      </p>
    </div>
    
    <div class="mb-4">
      <h4 class="text-sm font-medium mb-2">Next Run Times</h4>
      <div class="space-y-1">
        <div v-for="run in nextRuns" :key="run.time" class="text-sm text-gray-600 dark:text-gray-400">
          {{ run.description }}
        </div>
      </div>
    </div>
    
    <div class="flex gap-2">
      <button 
        @click="save"
        :disabled="!isValid"
        class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
      >
        Save Schedule
      </button>
      <button 
        @click="$emit('cancel')"
        class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
      >
        Cancel
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, watchEffect } from 'vue'
import { api } from '../composables/api'

export default {
  name: 'IntervalScheduler',
  props: {
    scriptSafeName: {
      type: String,
      required: true
    },
    initialSeconds: {
      type: Number,
      default: 3600
    },
    editingTrigger: {
      type: Object,
      default: null
    }
  },
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    const interval = ref({ // interval is a ref to an object
      value: 1,
      unit: 'hours'
    })
    
    const presets = [
      { label: '30 seconds', value: 30, unit: 'seconds' },
      { label: '1 minute', value: 1, unit: 'minutes' },
      { label: '5 minutes', value: 5, unit: 'minutes' },
      { label: '15 minutes', value: 15, unit: 'minutes' },
      { label: '30 minutes', value: 30, unit: 'minutes' },
      { label: '1 hour', value: 1, unit: 'hours' },
      { label: '6 hours', value: 6, unit: 'hours' },
      { label: '12 hours', value: 12, unit: 'hours' },
      { label: '1 day', value: 1, unit: 'days' },
      { label: '1 week', value: 7, unit: 'days' }
    ]
    
    const unitMultipliers = {
      seconds: 1,
      minutes: 60,
      hours: 3600,
      days: 86400
    }
    
    const totalSeconds = computed(() => {
      return interval.value.value * unitMultipliers[interval.value.unit]
    })
    
    const intervalDescription = computed(() => {
      if (interval.value.value === 1) {
        // Remove 's' from unit if value is 1 (e.g., "1 hour" instead of "1 hours")
        return `Run every ${interval.value.unit.endsWith('s') ? interval.value.unit.slice(0, -1) : interval.value.unit}`
      } else {
        return `Run every ${interval.value.value} ${interval.value.unit}`
      }
    })
    
    const isValid = computed(() => {
      return interval.value.value > 0 && totalSeconds.value > 0
    })
    
    const nextRuns = ref([])
    
    // Watch for changes and update next run times
    watch(() => interval.value, calculateNextRuns, { deep: true })
    
    // Ensure interval has valid properties
    watchEffect(() => {
      if (typeof interval.value.value !== 'number' || interval.value.value <= 0) {
        interval.value.value = 1
      }
      if (typeof interval.value.unit !== 'string' || !unitMultipliers[interval.value.unit]) {
        interval.value.unit = 'hours'
      }
    })
    
    function applyPreset(preset) {
      interval.value.value = preset.value
      interval.value.unit = preset.unit
    }
    
    function calculateNextRuns() {
      try {
        const now = new Date()
        const runs = []
        
        // Ensure totalSeconds is valid
        if (!totalSeconds.value || totalSeconds.value <= 0) {
          nextRuns.value = []
          return
        }
        
        for (let i = 1; i <= 5; i++) {
          const nextTime = new Date(now.getTime() + (totalSeconds.value * 1000 * i))
          runs.push({
            time: nextTime.toISOString(),
            description: nextTime.toLocaleString()
          })
        }
        
        nextRuns.value = runs
      } catch (error) {
        console.error('Error calculating next runs:', error)
        nextRuns.value = []
      }
    }
    
    async function save() {
      if (!isValid.value) return
      
      try {
        // First get the script ID from the safe name
        const scriptsResponse = await api.get('/api/scripts')
        const script = scriptsResponse.data.find(s => s.safe_name === props.scriptSafeName)
        
        if (!script) {
          console.error('Script not found with safe_name:', props.scriptSafeName)
          return
        }
        
        let response
        if (props.editingTrigger) {
          // Update existing trigger
          response = await api.put(`/api/execution/triggers/${props.editingTrigger.id}`, {
            script_id: script.id,
            trigger_type: 'interval',
            config: {
              seconds: totalSeconds.value
            },
            enabled: true
          })
        } else {
          // Create new trigger
          response = await api.post('/api/execution/triggers', {
            script_id: script.id,
            trigger_type: 'interval',
            config: {
              seconds: totalSeconds.value
            },
            enabled: true
          })
        }
        
        emit('save', response.data)
      } catch (error) {
        console.error('Error saving trigger:', error)
        console.error('Error details:', error.response?.data)
      }
    }
    
    // Initialize from props
    function initializeFromSeconds(seconds) {
      try {
        // Ensure we have a valid number
        const validSeconds = Math.max(1, parseInt(seconds) || 3600)
        
        if (validSeconds % 86400 === 0) {
          interval.value.value = validSeconds / 86400
          interval.value.unit = 'days'
        } else if (validSeconds % 3600 === 0) {
          interval.value.value = validSeconds / 3600
          interval.value.unit = 'hours'
        } else if (validSeconds % 60 === 0) {
          interval.value.value = validSeconds / 60
          interval.value.unit = 'minutes'
        } else {
          interval.value.value = validSeconds
          interval.value.unit = 'seconds'
        }
      } catch (error) {
        console.error('Error initializing from seconds:', error)
        // Fallback to default
        interval.value.value = 1
        interval.value.unit = 'hours'
      }
    }
    
    // Initialize
    initializeFromSeconds(props.initialSeconds)
    calculateNextRuns()
    
    
    return {
      interval,
      presets,
      totalSeconds,
      intervalDescription,
      isValid,
      nextRuns,
      applyPreset,
      save
    }
  }
}
</script>

<style scoped>
.interval-scheduler {
  max-width: 600px;
}
</style>