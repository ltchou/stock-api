import axios, { AxiosError } from 'axios'
import { ElNotification } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 90000, // 90秒
  headers: {
    'Content-Type': 'application/json'
  }
})

// 回應攔截器
api.interceptors.response.use(
  response => {
    // 檢查是否有警告訊息（206 Partial Content）
    if (response.status === 206 && response.data?.warning) {
      ElNotification({
        title: '警告',
        message: response.data.warning,
        type: 'warning',
        duration: 8000
      })
    }
    return response
  },
  (error: AxiosError) => {
    let message = '操作失敗'

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      message = '請求逾時，請稍後再試'
    } else if (error.response) {
      const status = error.response.status
      const data = error.response.data as { detail?: string }

      if (status === 429) {
        message = data.detail || 'API 流量已達上限，請稍後再試'
      } else if (status === 500) {
        message = data.detail || '伺服器錯誤（登入失敗或內部錯誤）'
      } else if (status === 504) {
        message = '操作逾時，請稍後再試'
      } else if (status === 422) {
        message = data.detail || '參數驗證失敗'
      } else if (status === 400) {
        message = data.detail || '參數錯誤'
      } else {
        message = data.detail || `錯誤代碼: ${status}`
      }
    }

    ElNotification({
      title: '錯誤',
      message,
      type: 'error',
      duration: 5000
    })

    return Promise.reject(error)
  }
)

export default api
