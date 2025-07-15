import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

export function useDateTime() {
  const authStore = useAuthStore()
  
  // Make timezone reactive
  const userTimezone = computed(() => authStore.user?.timezone || 'UTC')
  
  const formatDateTime = (dateString) => {
    if (!dateString) return ''
    
    const date = new Date(dateString)
    
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZone: userTimezone.value,
      timeZoneName: 'short'
    })
  }
  
  const formatDateTimeShort = (dateString) => {
    if (!dateString) return ''
    
    const date = new Date(dateString)
    
    const dateOptions = {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      timeZone: userTimezone.value
    }
    
    const timeOptions = {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: userTimezone.value
    }
    
    return date.toLocaleDateString('en-US', dateOptions) + ' ' + date.toLocaleTimeString('en-US', timeOptions)
  }
  
  const formatDate = (dateString) => {
    if (!dateString) return ''
    
    const date = new Date(dateString)
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      timeZone: userTimezone.value
    })
  }
  
  return {
    formatDateTime,
    formatDateTimeShort,
    formatDate,
    userTimezone
  }
}