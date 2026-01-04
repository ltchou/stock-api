import { createRouter, createWebHistory } from 'vue-router'
import ScannerView from '@/views/ScannerView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'scanner',
      component: ScannerView
    }
  ]
})

export default router
