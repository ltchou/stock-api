export interface ScanRequest {
  scanner_type: string
  date: string
  count: number
  ascending: boolean
  simulation: boolean
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
}
