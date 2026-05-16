<template>
  <div ref="scannerContainer" class="scanner-container">
    <el-card class="scanner-card">
      <template #header>
        <div class="card-header">
          <span>股票掃描器</span>
          <span class="version">v{{ appVersion }}</span>
        </div>
      </template>

      <!-- 掃描表單 -->
      <el-form :model="formData" label-width="120px">
        <el-form-item label="掃描器類型">
          <el-select v-model="formData.scanner_type" placeholder="請選擇掃描器類型">
            <el-option label="漲跌幅排名" value="ChangePercentRank" />
            <el-option label="成交量排名" value="VolumeRank" />
            <el-option label="金額排名" value="AmountRank" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="選擇日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledWeekends"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="查詢數量">
          <el-slider v-model="formData.count" :min="1" :max="200" show-input />
          <span class="form-hint">從 Shioaji API 取得的資料筆數（最多 200 筆）</span>
        </el-form-item>

        <el-form-item label="排序方式">
          <el-switch v-model="formData.ascending" active-text="升序" inactive-text="降序" />
        </el-form-item>

        <el-form-item label="模擬模式">
          <el-switch
            v-model="formData.simulation"
            active-text="開啟"
            inactive-text="關閉"
            disabled
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="store.loading"
            :disabled="!formData.date"
            @click="handleScan"
          >
            {{ store.loading ? '掃描中...' : '開始掃描' }}
          </el-button>
          <el-button v-if="store.results.length > 0" :loading="store.loading" @click="handleExport">
            匯出 CSV
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 結果統計 -->
      <div v-if="store.results.length > 0" class="stats">
        <el-tag type="success">共 {{ store.totalCount }} 筆資料</el-tag>
        <el-tag type="info">執行時間: {{ store.executionTime.toFixed(2) }}秒</el-tag>
        <el-tag v-if="paginatedData.length < store.results.length" type="warning">
          顯示第 {{ (formData.page! - 1) * formData.page_size! + 1 }} -
          {{ Math.min(formData.page! * formData.page_size!, store.results.length) }} 筆
        </el-tag>
      </div>

      <!-- 結果表格 -->
      <el-table
        v-if="store.results.length > 0"
        :data="paginatedData"
        stripe
        border
        style="width: 100%; margin-top: 20px"
        max-height="600"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="code" label="股票代碼" width="120" fixed sortable="custom" />
        <el-table-column prop="name" label="股票名稱" sortable="custom" />
        <el-table-column prop="close" label="收盤價" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            {{ row.close?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="change_price"
          label="漲跌"
          width="100"
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span
              v-if="row.change_price !== undefined && row.change_price !== null"
              :class="row.change_price >= 0 ? 'market-up' : 'market-down'"
            >
              {{ row.change_price >= 0 ? '+' : '' }}{{ row.change_price.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="change_percent"
          label="漲跌幅"
          width="100"
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span
              v-if="calculateChangePercent(row) !== null"
              :class="getChangePercentClass(calculateChangePercent(row)!)"
            >
              {{ calculateChangePercent(row)! >= 0 ? '+' : ''
              }}{{ calculateChangePercent(row)!.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="open" label="開盤價" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            {{ row.open?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="high" label="最高價" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            {{ row.high?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="low" label="最低價" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            {{ row.low?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total_volume"
          label="總量"
          width="130"
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            {{ row.total_volume?.toLocaleString() ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total_amount"
          label="總金額"
          width="150"
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.total_amount !== undefined && row.total_amount !== null">
              {{ formatAmount(row.total_amount) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分頁控制項 -->
      <el-pagination
        v-if="store.results.length > 0"
        v-model:current-page="formData.page"
        v-model:page-size="formData.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="store.results.length"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: center"
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, nextTick, onMounted, ref } from 'vue'
import { useScannerStore } from '@/stores/scanner'
import { ElNotification } from 'element-plus'
import type { ScanRequest, StockData } from '@/api/types'

// 宣告全域變數
declare const __APP_VERSION__: string

// 將全域變數儲存為 component 常數，避免 Vue 警告
const appVersion = __APP_VERSION__

const store = useScannerStore()
const scannerContainer = ref<globalThis.HTMLElement | null>(null)
const sortState = reactive<{
  prop: string
  order: 'ascending' | 'descending' | null
}>({
  prop: '',
  order: null
})

const formData = reactive<ScanRequest>({
  scanner_type: 'ChangePercentRank',
  date: '',
  count: 10,
  ascending: false, // 預設為 false（降序，從大到小）
  simulation: true,
  page: 1, // 當前頁碼
  page_size: 20 // 每頁顯示筆數
})

const formatLocalDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

onMounted(() => {
  // 設定預設日期為今天，若今天是週末則設定為上個週五
  const today = new Date()
  const day = today.getDay()

  // 如果是週日（0），往前推2天到週五
  if (day === 0) {
    today.setDate(today.getDate() - 2)
  }
  // 如果是週六（6），往前推1天到週五
  else if (day === 6) {
    today.setDate(today.getDate() - 1)
  }

  formData.date = formatLocalDate(today)
})

const disabledWeekends = (date: Date) => {
  // 禁用週六（6）和週日（0）
  const day = date.getDay()
  return day === 0 || day === 6
}

const getSortValue = (row: StockData, prop: string): string | number | null => {
  if (prop === 'change_percent') {
    return calculateChangePercent(row)
  }

  const value = row[prop]
  if (typeof value === 'number' || typeof value === 'string') {
    return value
  }

  return null
}

const sortedData = computed(() => {
  if (!sortState.prop || !sortState.order) {
    return store.results
  }

  const direction = sortState.order === 'ascending' ? 1 : -1
  return [...store.results].sort((a, b) => {
    const aValue = getSortValue(a, sortState.prop)
    const bValue = getSortValue(b, sortState.prop)

    if (aValue === null && bValue === null) return 0
    if (aValue === null) return 1
    if (bValue === null) return -1

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return (aValue - bValue) * direction
    }

    return (
      String(aValue).trim().localeCompare(String(bValue).trim(), 'zh-Hant', { numeric: true }) *
      direction
    )
  })
})

// 計算當前頁的資料
const paginatedData = computed(() => {
  if (!formData.page || !formData.page_size) {
    return sortedData.value
  }
  const start = (formData.page - 1) * formData.page_size
  const end = start + formData.page_size
  return sortedData.value.slice(start, end)
})

const scrollToTop = () => {
  nextTick(() => {
    scannerContainer.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

const handleSortChange = ({
  prop,
  order
}: {
  prop: string
  order: 'ascending' | 'descending' | null
}) => {
  sortState.prop = prop
  sortState.order = order
  formData.page = 1
  scrollToTop()
}

const handlePageChange = () => {
  scrollToTop()
}

const handlePageSizeChange = () => {
  formData.page = 1
  scrollToTop()
}

const handleScan = async () => {
  try {
    // 重置頁碼到第一頁
    formData.page = 1
    await store.scan(formData)
    ElNotification({
      title: '成功',
      message: `成功掃描 ${store.totalCount} 筆股票資料`,
      type: 'success',
      duration: 3000
    })
  } catch {
    // 錯誤已在 API 攔截器中處理
  }
}

const handleExport = async () => {
  try {
    await store.exportToCSV(formData)
    ElNotification({
      title: '成功',
      message: 'CSV 檔案已下載',
      type: 'success',
      duration: 3000
    })
  } catch {
    // 錯誤已在 API 攔截器中處理
  }
}

// 格式化金額（轉換為億、萬等單位）
const formatAmount = (amount: number): string => {
  if (amount >= 100000000) {
    // 大於 1 億
    return (amount / 100000000).toFixed(2) + '億'
  } else if (amount >= 10000) {
    // 大於 1 萬
    return (amount / 10000).toFixed(2) + '萬'
  } else {
    return amount.toLocaleString()
  }
}

// 計算漲跌幅（用收盤價和漲跌價差計算）
const calculateChangePercent = (row: StockData): number | null => {
  // 如果已有 change_percent，直接返回
  if (row.change_percent !== undefined && row.change_percent !== null) {
    return row.change_percent
  }

  // 否則用收盤價和漲跌計算
  if (
    row.close !== undefined &&
    row.close !== null &&
    row.change_price !== undefined &&
    row.change_price !== null
  ) {
    const yesterday_close = row.close - row.change_price
    if (yesterday_close !== 0) {
      return (row.change_price / yesterday_close) * 100
    }
  }

  return null
}

const getChangePercentClass = (changePercent: number): string => {
  if (changePercent >= 9.9) {
    return 'limit-up'
  }
  if (changePercent <= -9.9) {
    return 'limit-down'
  }
  return changePercent >= 0 ? 'market-up' : 'market-down'
}
</script>

<style scoped>
.scanner-container {
  --finance-ink: #f4f7f8;
  --finance-muted: #b9c7cc;
  --finance-border: #30484f;
  --finance-panel: #111f25;
  --finance-panel-soft: #172a31;
  --finance-primary: #38bdf8;
  --finance-primary-hover: #7dd3fc;
  --finance-up: #ff8a80;
  --finance-down: #45d483;
  --finance-limit-up: #c62828;
  --finance-limit-down: #087443;
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
  color: var(--finance-ink);
}

.scanner-card {
  background: var(--finance-panel);
  border: 1px solid var(--finance-border);
  border-radius: 8px;
  box-shadow: 0 22px 48px rgba(0, 0, 0, 0.42);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
  color: var(--finance-ink);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0;
}

.version {
  font-size: 12px;
  font-weight: 600;
  color: #e8f5f8;
  background: #18333c;
  border: 1px solid #3c5d66;
  border-radius: 999px;
  padding: 2px 8px;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.form-hint {
  font-size: 12px;
  color: var(--finance-muted);
  margin-left: 10px;
}

.market-up {
  color: var(--finance-up);
  font-weight: 700;
}

.market-down {
  color: var(--finance-down);
  font-weight: 700;
}

.limit-up,
.limit-down {
  display: inline-flex;
  min-width: 64px;
  justify-content: center;
  border-radius: 4px;
  color: #ffffff;
  font-weight: 800;
  line-height: 1.45;
  padding: 1px 6px;
}

.limit-up {
  background: var(--finance-limit-up);
}

.limit-down {
  background: var(--finance-limit-down);
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--finance-border);
  background: linear-gradient(180deg, #172b32 0%, #102026 100%);
}

:deep(.el-form) {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 8px 22px;
  padding-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 14px;
}

:deep(.el-form-item__label) {
  color: #dce8eb;
  font-weight: 700;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: #0d1a20;
  border-radius: 6px;
  box-shadow: 0 0 0 1px #45636d inset;
}

:deep(.el-input__inner),
:deep(.el-select__placeholder),
:deep(.el-select__selected-item) {
  color: var(--finance-ink);
}

:deep(.el-input__inner::placeholder) {
  color: #9eb0b7;
}

:deep(.el-slider__runway) {
  background-color: #405a63;
}

:deep(.el-slider__bar),
:deep(.el-slider__button) {
  background-color: var(--finance-primary);
  border-color: var(--finance-primary);
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--finance-primary);
  border-color: var(--finance-primary);
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--finance-primary);
  --el-button-border-color: var(--finance-primary);
  --el-button-hover-bg-color: var(--finance-primary-hover);
  --el-button-hover-border-color: var(--finance-primary-hover);
  --el-button-active-bg-color: #0284c7;
  --el-button-active-border-color: #0284c7;
  color: #061017;
  font-weight: 700;
}

:deep(.el-button:not(.el-button--primary)) {
  color: #d9f3ff;
  border-color: #4f7480;
  background: #13262d;
  font-weight: 700;
}

:deep(.el-table) {
  --el-table-bg-color: #0f1c22;
  --el-table-tr-bg-color: #0f1c22;
  --el-table-expanded-cell-bg-color: #0f1c22;
  --el-table-header-bg-color: #1a3038;
  --el-table-header-text-color: #f4f7f8;
  --el-table-text-color: #e7eef0;
  --el-table-row-hover-bg-color: #183039;
  --el-table-border-color: #30484f;
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #13252c;
}

:deep(.el-table th.el-table__cell) {
  font-weight: 800;
}

:deep(.el-table .cell) {
  line-height: 1.45;
}

:deep(.el-tag) {
  color: #f4f7f8;
  border-radius: 6px;
  font-weight: 700;
}

:deep(.el-tag--success) {
  background-color: #12392d;
  border-color: #2f8f69;
}

:deep(.el-tag--info) {
  background-color: #18333c;
  border-color: #4c7580;
}

:deep(.el-tag--warning) {
  background-color: #473311;
  border-color: #b8892e;
}

:deep(.el-pagination) {
  color: var(--finance-ink);
}

:deep(.el-pagination button),
:deep(.el-pager li) {
  color: var(--finance-ink);
  background: #111f25;
  border: 1px solid #405a63;
}

:deep(.el-pager li.is-active) {
  color: #061017;
  background: var(--finance-primary);
  border-color: var(--finance-primary);
}

@media (max-width: 760px) {
  .scanner-container {
    padding: 12px;
  }

  :deep(.el-form) {
    grid-template-columns: 1fr;
  }

  .stats {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
