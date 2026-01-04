<template>
  <div class="scanner-container">
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

        <el-form-item label="數量">
          <el-slider v-model="formData.count" :min="1" :max="50" show-input />
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
      </div>

      <!-- 結果表格 -->
      <el-table
        v-if="store.results.length > 0"
        :data="store.results"
        stripe
        border
        style="width: 100%; margin-top: 20px"
        max-height="600"
      >
        <el-table-column prop="code" label="股票代碼" width="120" fixed />
        <el-table-column prop="name" label="股票名稱" width="120" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="open" label="開盤價" width="100" align="right">
          <template #default="{ row }">
            {{ row.open?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="close" label="收盤價" width="100" align="right">
          <template #default="{ row }">
            {{ row.close?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="high" label="最高價" width="100" align="right">
          <template #default="{ row }">
            {{ row.high?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="low" label="最低價" width="100" align="right">
          <template #default="{ row }">
            {{ row.low?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量" width="120" align="right">
          <template #default="{ row }">
            {{ row.volume?.toLocaleString() ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="change_percent" label="漲跌幅 %" width="120" align="right">
          <template #default="{ row }">
            <span
              v-if="row.change_percent !== undefined && row.change_percent !== null"
              :style="{ color: row.change_percent >= 0 ? 'red' : 'green' }"
            >
              {{ row.change_percent >= 0 ? '+' : '' }}{{ row.change_percent.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="rank_value" label="排名值" width="120" align="right">
          <template #default="{ row }">
            <span
              v-if="row.rank_value !== undefined && row.rank_value !== null"
              :style="{ color: row.rank_value >= 0 ? 'red' : 'green' }"
            >
              {{ row.rank_value >= 0 ? '+' : '' }}{{ row.rank_value.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useScannerStore } from '@/stores/scanner'
import { ElNotification } from 'element-plus'
import type { ScanRequest } from '@/api/types'

// 宣告全域變數
declare const __APP_VERSION__: string

// 將全域變數儲存為 component 常數，避免 Vue 警告
const appVersion = __APP_VERSION__

const store = useScannerStore()

const formData = reactive<ScanRequest>({
  scanner_type: 'ChangePercentRank',
  date: '',
  count: 10,
  ascending: false,
  simulation: true
})

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

  formData.date = today.toISOString().split('T')[0] as string
})

const disabledWeekends = (date: Date) => {
  // 禁用週六（6）和週日（0）
  const day = date.getDay()
  return day === 0 || day === 6
}

const handleScan = async () => {
  try {
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
</script>

<style scoped>
.scanner-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.scanner-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.version {
  font-size: 12px;
  font-weight: normal;
  color: #909399;
}

.stats {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
</style>
