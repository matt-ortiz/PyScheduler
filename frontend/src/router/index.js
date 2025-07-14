import { createRouter, createWebHistory } from 'vue-router'
import ScriptList from '../views/ScriptList.vue'
import ScriptEditor from '../views/ScriptEditor.vue'
import LogsView from '../views/LogsView.vue'
import Settings from '../views/Settings.vue'
import Login from '../views/Login.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    name: 'ScriptList',
    component: ScriptList,
    meta: { requiresAuth: true }
  },
  {
    path: '/script/:safeName?',
    name: 'ScriptEditor',
    component: ScriptEditor,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'LogViewer',
    component: LogsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      next('/login')
      return
    }
  }
  
  // Check if route requires guest (not authenticated)
  if (to.meta.requiresGuest) {
    if (authStore.isAuthenticated) {
      next('/')
      return
    }
  }
  
  next()
})

export default router