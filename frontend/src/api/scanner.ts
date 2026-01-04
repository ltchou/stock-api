import api from './index'
import type { ScanRequest, ScanResponse } from './types'

/**
 * 執行股票掃描
 */
export const scanStocks = async (request: ScanRequest): Promise<ScanResponse> => {
  const response = await api.post<ScanResponse>('/scan', request)
  return response.data
}

/**
 * 匯出 CSV
 */
export const exportCSV = async (request: ScanRequest): Promise<Blob> => {
  const response = await api.post('/export', request, {
    responseType: 'blob'
  })
  return response.data
}
