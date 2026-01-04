import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StockData, ScanRequest } from '@/api/types'
import { scanStocks, exportCSV } from '@/api/scanner'

export const useScannerStore = defineStore('scanner', () => {
  const loading = ref(false)
  const results = ref<StockData[]>([])
  const executionTime = ref(0)
  const totalCount = ref(0)

  /**
   * 執行掃描
   */
  const scan = async (request: ScanRequest) => {
    loading.value = true
    try {
      const response = await scanStocks(request)
      results.value = response.data
      executionTime.value = response.execution_time
      totalCount.value = response.total_count
      return response
    } finally {
      loading.value = false
    }
  }

  /**
   * 匯出 CSV
   */
  const exportToCSV = async (request: ScanRequest) => {
    loading.value = true
    try {
      const blob = await exportCSV(request)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `stock_scan_${request.date}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    results,
    executionTime,
    totalCount,
    scan,
    exportToCSV
  }
})
