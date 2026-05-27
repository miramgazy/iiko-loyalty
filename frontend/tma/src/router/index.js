import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { safeStorage } from '@/services/storage'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/onboarding/lang',
    name: 'onboarding-lang',
    component: () => import('@/views/LanguageSelectionView.vue'),
  },
  {
    path: '/onboarding/phone',
    name: 'onboarding-phone',
    component: () => import('@/views/PhoneInputView.vue'),
  },
  {
    path: '/onboarding/consent',
    name: 'onboarding-consent',
    component: () => import('@/views/BotConsentView.vue'),
  },
  {
    path: '/info',
    name: 'info',
    component: () => import('@/views/InfoView.vue'),
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory('/tma/'),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  // If not authenticated yet (loading state), allow navigation
  if (auth.isLoading) return next()

  // If not authenticated, stay on current page (auth happens in App.vue)
  if (!auth.isAuthenticated && to.name !== 'home') return next('/')

  // If authenticated but not onboarded (no phone yet)
  if (auth.isAuthenticated && !auth.isOnboarded) {
    const langSelected = safeStorage.getItem('tma_lang_selected') === 'true'
    
    if (!langSelected && to.name !== 'onboarding-lang') {
      return next('/onboarding/lang')
    }
    if (langSelected && to.name === 'onboarding-lang') {
      return next('/onboarding/phone')
    }
    if (to.name !== 'onboarding-lang' && to.name !== 'onboarding-phone') {
      return next(langSelected ? '/onboarding/phone' : '/onboarding/lang')
    }
  }

  // Consent page: only redirect there if user is onboarded but needs consent
  // AND they're trying to reach the home page (not info/profile, which should always work)
  if (auth.isAuthenticated && auth.isOnboarded && auth.needsConsent) {
    if (to.name === 'home') {
      // Only redirect on navigation to home, not blocking /info or /profile
      return next('/onboarding/consent')
    }
    // Allow navigation to consent page itself
    if (to.name === 'onboarding-consent') {
      return next()
    }
    // For /info, /profile and other pages — allow, don't block
  }

  // If already onboarded and consent status decided, don't allow accessing onboarding pages
  if (auth.isAuthenticated && auth.isOnboarded && !auth.needsConsent && 
      (to.name === 'onboarding-phone' || to.name === 'onboarding-lang' || to.name === 'onboarding-consent')) {
    return next('/')
  }

  next()
})

export default router
