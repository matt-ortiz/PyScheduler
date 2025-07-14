import { defineStore } from 'pinia'
import { api } from '../composables/api'

export const useScriptStore = defineStore('scripts', {
  state: () => ({
    scripts: [],
    folders: [],
    currentScript: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getScriptById: (state) => (id) => {
      return state.scripts.find(script => script.id === parseInt(id))
    },
    
    getScriptBySafeName: (state) => (safeName) => {
      return state.scripts.find(script => script.safe_name === safeName)
    },
    
    getScriptsByFolder: (state) => (folderId) => {
      return state.scripts.filter(script => script.folder_id === folderId)
    },
    
    getScriptsWithoutFolder: (state) => {
      return state.scripts.filter(script => !script.folder_id)
    }
  },
  
  actions: {
    async fetchScripts() {
      this.loading = true
      this.error = null
      try {
        const response = await api.get('/api/scripts')
        this.scripts = response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch scripts'
        console.error('Error fetching scripts:', error)
      } finally {
        this.loading = false
      }
    },
    
    async fetchFolders() {
      try {
        const response = await api.get('/api/folders')
        this.folders = response.data
      } catch (error) {
        console.error('Error fetching folders:', error)
      }
    },
    
    async createScript(scriptData) {
      try {
        const response = await api.post('/api/scripts', scriptData)
        this.scripts.push(response.data)
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to create script')
      }
    },
    
    async updateScript(safeName, scriptData) {
      try {
        const response = await api.put(`/api/scripts/${safeName}`, scriptData)
        const index = this.scripts.findIndex(s => s.safe_name === safeName)
        if (index !== -1) {
          // Fetch the updated script to get all fields
          const updatedScript = await this.fetchScript(safeName)
          this.scripts[index] = updatedScript
        }
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to update script')
      }
    },
    
    async fetchScript(safeName) {
      try {
        const response = await api.get(`/api/scripts/${safeName}`)
        this.currentScript = response.data
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to fetch script')
      }
    },
    
    async executeScript(safeName) {
      try {
        const response = await api.post(`/api/scripts/${safeName}/execute`)
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to execute script')
      }
    },
    
    async deleteScript(safeName) {
      try {
        await api.delete(`/api/scripts/${safeName}`)
        this.scripts = this.scripts.filter(s => s.safe_name !== safeName)
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to delete script')
      }
    },
    
    async autoSaveScript(safeName, content) {
      try {
        await api.patch(`/api/scripts/${safeName}/auto-save`, { content })
      } catch (error) {
        console.error('Auto-save failed:', error)
      }
    },
    
    async createFolder(folderData) {
      try {
        const response = await api.post('/api/folders', folderData)
        this.folders.push(response.data)
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to create folder')
      }
    }
  }
})