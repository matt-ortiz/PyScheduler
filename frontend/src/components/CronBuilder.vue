<template>
  <div class="cron-builder">
    <h3 class="text-lg font-semibold mb-4">CRON Expression Builder</h3>
    
    <!-- Quick presets -->
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
    
    <!-- Manual builder -->
    <div class="grid grid-cols-5 gap-4 mb-4">
      <div>
        <label class="block text-sm font-medium mb-1">Minute</label>
        <select v-model="cron.minute" class="w-full p-2 border rounded dark:bg-gray-800">
          <option value="*">* (every)</option>
          <option v-for="i in 60" :key="i-1" :value="i-1">{{ i-1 }}</option>
        </select>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Hour</label>
        <select v-model="cron.hour" class="w-full p-2 border rounded dark:bg-gray-800">
          <option value="*">* (every)</option>
          <option v-for="i in 24" :key="i-1" :value="i-1">{{ i-1 }}</option>
        </select>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Day</label>
        <select v-model="cron.day" class="w-full p-2 border rounded dark:bg-gray-800">
          <option value="*">* (every)</option>
          <option v-for="i in 31" :key="i" :value="i">{{ i }}</option>
        </select>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Month</label>
        <select v-model="cron.month" class="w-full p-2 border rounded dark:bg-gray-800">
          <option value="*">* (every)</option>
          <option v-for="(month, i) in months" :key="i+1" :value="i+1">{{ i+1 }} ({{ month }})</option>
        </select>
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Weekday</label>
        <select v-model="cron.weekday" class="w-full p-2 border rounded dark:bg-gray-800">
          <option value="*">* (every)</option>
          <option v-for="(day, i) in weekdays" :key="i" :value="i">{{ i }} ({{ day }})</option>
        </select>
      </div>
    </div>
    
    <!-- Generated expression -->
    <div class="mb-4">
      <label class="block text-sm font-medium mb-1">CRON Expression</label>
      <div class="flex gap-2">
        <input 
          v-model="cronExpression" 
          @input="validateExpression"
          class="flex-1 p-2 border rounded dark:bg-gray-800 font-mono"
          placeholder="0 0 * * *"
        />
        <button 
          @click="validateExpression"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Validate
        </button>
      </div>
      <div v-if="validation.error" class="text-red-500 text-sm mt-1">
        {{ validation.error }}
      </div>
    </div>
    
    <!-- Description -->
    <div class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded">
      <p class="text-sm">
        <strong>Description:</strong> {{ cronDescription }}
      </p>
    </div>
    
    <!-- Next run times -->
    <div v-if="nextRuns.length > 0" class="mb-4">
      <h4 class="text-sm font-medium mb-2">Next Run Times</h4>
      <div class="space-y-1">
        <div v-for="run in nextRuns" :key="run.time" class="text-sm text-gray-600 dark:text-gray-400">
          {{ run.description }}
        </div>
      </div>
    </div>
    
    <!-- Actions -->
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
import { ref, computed, watch } from 'vue'
import { api } from '../composables/api'

export default {
  name: 'CronBuilder',
  props: {
    scriptId: {
      type: Number,
      required: true
    },
    initialExpression: {
      type: String,
      default: '0 0 * * *'
    }
  },
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    const cron = ref({
      minute: '0',
      hour: '0',
      day: '*',
      month: '*',
      weekday: '*'
    })
    
    const cronExpression = ref(props.initialExpression)
    const validation = ref({ valid: false, error: null })
    const nextRuns = ref([])
    
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    
    const weekdays = [
      'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'
    ]
    
    const presets = [
      { label: 'Every minute', expression: '* * * * *' },
      { label: 'Every hour', expression: '0 * * * *' },
      { label: 'Every day at midnight', expression: '0 0 * * *' },
      { label: 'Every day at 9 AM', expression: '0 9 * * *' },
      { label: 'Every Monday at 9 AM', expression: '0 9 * * 1' },
      { label: 'Every 1st of month', expression: '0 0 1 * *' },
      { label: 'Every 15 minutes', expression: '*/15 * * * *' },
      { label: 'Every 30 minutes', expression: '*/30 * * * *' },
      { label: 'Every 6 hours', expression: '0 */6 * * *' }
    ]
    
    const cronDescription = computed(() => {
      const parts = cronExpression.value.split(' ')
      if (parts.length !== 5) return 'Invalid expression'
      
      const [min, hour, day, month, weekday] = parts
      
      let desc = 'Run '
      
      // Frequency
      if (min === '*' && hour === '*' && day === '*' && month === '*' && weekday === '*') {
        desc += 'every minute'
      } else if (hour === '*' && day === '*' && month === '*' && weekday === '*') {
        desc += min === '*' ? 'every minute' : `at minute ${min} of every hour`
      } else if (day === '*' && month === '*' && weekday === '*') {
        desc += `at ${hour}:${min.padStart(2, '0')} every day`
      } else if (month === '*' && weekday === '*') {
        desc += `at ${hour}:${min.padStart(2, '0')} on day ${day} of every month`
      } else {
        desc += `at ${hour}:${min.padStart(2, '0')}`
        if (day !== '*') desc += ` on day ${day}`
        if (month !== '*') desc += ` of month ${month}`
        if (weekday !== '*') desc += ` on ${weekdays[weekday]}`
      }
      
      return desc
    })
    
    const isValid = computed(() => validation.value.valid)
    
    // Watch for changes in cron object and update expression
    watch(cron, () => {
      cronExpression.value = `${cron.value.minute} ${cron.value.hour} ${cron.value.day} ${cron.value.month} ${cron.value.weekday}`
    }, { deep: true })
    
    // Watch for changes in expression and validate
    watch(cronExpression, validateExpression)
    
    function applyPreset(preset) {
      cronExpression.value = preset.expression
      parseCronExpression()
    }
    
    function parseCronExpression() {
      const parts = cronExpression.value.split(' ')
      if (parts.length === 5) {
        cron.value.minute = parts[0]
        cron.value.hour = parts[1]
        cron.value.day = parts[2]
        cron.value.month = parts[3]
        cron.value.weekday = parts[4]
      }
    }
    
    async function validateExpression() {
      if (!cronExpression.value || cronExpression.value.trim() === '') {
        validation.value = { valid: false, error: 'CRON expression is required' }
        nextRuns.value = []
        return
      }
      
      try {
        const response = await api.post('/api/execution/validate-cron', {
          expression: cronExpression.value
        })
        
        validation.value = { valid: true, error: null }
        nextRuns.value = response.data.next_runs || []
      } catch (error) {
        validation.value = { 
          valid: false, 
          error: error.response?.data?.detail || 'Invalid CRON expression' 
        }
        nextRuns.value = []
      }
    }
    
    async function save() {
      if (!isValid.value) return
      
      if (!cronExpression.value || cronExpression.value.trim() === '') {
        return
      }
      
      console.log('CronBuilder save called with props.scriptId:', props.scriptId, 'type:', typeof props.scriptId)
      
      try {
        const requestPayload = {
          script_id: props.scriptId,
          trigger_type: 'cron',
          config: {
            expression: cronExpression.value
          },
          enabled: true
        }
        
        console.log('About to send request:', requestPayload)
        
        const response = await api.post('/api/execution/triggers', requestPayload)
        
        emit('save', response.data)
      } catch (error) {
        console.error('Error saving trigger:', error)
        console.error('Error details:', error.response?.data)
        console.error('Request payload was:', {
          script_id: props.scriptId,
          trigger_type: 'cron',
          config: {
            expression: cronExpression.value
          },
          enabled: true
        })
      }
    }
    
    // Initialize
    parseCronExpression()
    
    // Ensure expression is built from cron object after parsing
    cronExpression.value = `${cron.value.minute} ${cron.value.hour} ${cron.value.day} ${cron.value.month} ${cron.value.weekday}`
    
    validateExpression()
    
    return {
      cron,
      cronExpression,
      validation,
      nextRuns,
      months,
      weekdays,
      presets,
      cronDescription,
      isValid,
      applyPreset,
      validateExpression,
      save
    }
  }
}
</script>

<style scoped>
.cron-builder {
  max-width: 800px;
}
</style>