import { createRouter, createWebHistory } from 'vue-router'

import { useAssessmentStore } from '@/stores/assessment'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: () => import('@/views/StartView.vue') },
    {
      path: '/test/hardware',
      name: 'hardware',
      component: () => import('@/views/HardwareView.vue'),
    },
    { path: '/test/quiz', name: 'quiz', component: () => import('@/views/QuizView.vue') },
    { path: '/test/lab', name: 'lab', component: () => import('@/views/LabView.vue') },
    {
      path: '/result/:code',
      name: 'result',
      component: () => import('@/views/ResultView.vue'),
      props: true,
    },
    { path: '/stats', name: 'stats', component: () => import('@/views/StatsView.vue') },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

// Steps must be walked in order so the payload is never half-built.
router.beforeEach((to) => {
  const store = useAssessmentStore()
  // Hardware detection itself is skippable, but the step must be visited first.
  if (to.name === 'quiz' && !store.hardwareVisited) return { name: 'hardware' }
  if (to.name === 'lab' && !store.quizComplete) return { name: 'quiz' }
  return true
})
