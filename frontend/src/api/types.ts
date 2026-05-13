export interface ScanRequest {
  scanner_type: string
  date: string
  count: number
  ascending: boolean
  simulation: boolean
  page?: number // 前端分頁：當前頁碼（從 1 開始）
  page_size?: number // 前端分頁：每頁筆數
}

export interface StockData {
  code?: string
  name?: string
  date?: string
  open?: number
  close?: number
  high?: number
  low?: number
  volume?: number
  change_percent?: number
  change_price?: number
  rank_value?: number
  ts?: number
  [key: string]: string | number | undefined
}

export interface ScanResponse {
  status: string
  data: StockData[]
  total_count: number
  execution_time: number
  message?: string // 額外訊息（例如：從資料庫讀取）
}
