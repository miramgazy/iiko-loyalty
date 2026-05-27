import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/select-org',
    name: 'select-org',
    component: () => import('@/views/SelectOrgView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/superadmin',
    name: 'superadmin',
    component: () => import('@/views/SuperAdminDashboard.vue'),
    meta: { requiresAuth: true, requiresSuperAdmin: true },
  },
  {
    path: '/superadmin/users',
    name: 'superadmin-users',
    component: () => import('@/views/SuperAdminUsersView.vue'),
    meta: { requiresAuth: true, requiresSuperAdmin: true },
  },

  {
    path: '/admin/settings',
    name: 'org-settings',
    component: () => import('@/views/OrganizationSettingsView.vue'),
    meta: { requiresAuth: true, requiresOrgManager: true },
  },
  {
    path: '/admin/employees',
    name: 'employees',
    component: () => import('@/views/EmployeeListView.vue'),
    meta: { requiresAuth: true, requiresOrgManager: true },
  },
  {
    path: '/admin/customers',
    name: 'customers',
    component: () => import('@/views/CustomerListView.vue'),
    meta: { requiresAuth: true, requiresOrgAdmin: true },
  },
  {
    path: '/admin/mailings',
    name: 'mailings',
    component: () => import('@/views/MailingsView.vue'),
    meta: { requiresAuth: true, requiresOrgAdmin: true },
  },
  {
    path: '/',
    redirect: () => {
      const auth = useAuthStore()
      if (!auth.isAuthenticated) return '/login'
      if (auth.isSuperAdmin) return '/superadmin'
      if (auth.currentOrgId) return '/admin/customers'
      return '/select-org'
    },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) return next()

  if (!auth.isAuthenticated) return next('/login')

  if (to.meta.requiresSuperAdmin && !auth.isSuperAdmin) return next('/')
  if (to.meta.requiresOrgManager && !auth.isOrgManager) return next('/')
  if (to.meta.requiresOrgAdmin && !auth.isOrgAdmin) return next('/')

  // Redirect to org selector if no org selected and not superadmin
  if (!to.meta.requiresSuperAdmin && !auth.currentOrgId && !auth.isSuperAdmin) {
    return next('/select-org')
  }

  next()
})

export default router
