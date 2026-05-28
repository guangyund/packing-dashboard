<template>
  <div>
    <!-- KPI 卡片行 -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="card in kpiCards" :key="card.label">
        <div class="kpi-header">
          <span class="kpi-label">{{ card.label }}</span>
          <span class="kpi-badge" :style="{ background: card.badgeBg, color: card.color }">{{ card.badge }}</span>
        </div>
        <div class="kpi-value" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="kpi-sub">{{ card.sub }}</div>
      </div>
    </div>

    <!-- 时间范围 + 趋势图 -->
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px">
      <el-button-group size="small">
        <el-button :type="days===7  ? 'primary' : ''" @click="changeDays(7)">近 7 天</el-button>
        <el-button :type="days===14 ? 'primary' : ''" @click="changeDays(14)">近 14 天</el-button>
        <el-button :type="days===30 ? 'primary' : ''" @click="changeDays(30)">近 30 天</el-button>
      </el-button-group>
    </div>

    <el-card shadow="never" header="异常趋势（各类型）" style="margin-bottom:16px">
      <div ref="trendChart" style="height:240px"></div>
    </el-card>

    <!-- 明细查询 -->
    <el-card shadow="never" header="异常明细">
      <!-- 过滤栏 -->
      <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;align-items:center">
        <el-select v-model="filter.anomaly_type" placeholder="全部类型" clearable size="small" style="width:140px">
          <el-option label="AI调用失败" value="ai_failure" />
          <el-option label="计算结果异常" value="calc_anomaly" />
          <el-option label="计算超时" value="calc_timeout" />
        </el-select>
        <el-select v-model="filter.severity" placeholder="全部级别" clearable size="small" style="width:120px">
          <el-option label="critical" value="critical" />
          <el-option label="error" value="error" />
          <el-option label="warning" value="warning" />
        </el-select>
        <el-date-picker
          v-model="filter.dateRange" type="daterange"
          range-separator="→" start-placeholder="开始日期" end-placeholder="结束日期"
          size="small" style="width:240px" value-format="YYYY-MM-DD"
        />
        <el-button size="small" type="primary" @click="handleQuery">查询</el-button>
        <el-button size="small" @click="resetFilter">重置</el-button>
      </div>

      <el-table :data="listRows" v-loading="listLoading" size="small" style="width:100%" class="anomaly-table">
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ row.created_at || '—' }}</template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.anomaly_type)" size="small">{{ typeLabel(row.anomaly_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="85">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="计算编号" width="150">
          <template #default="{ row }">
            <span v-if="row.calc_no" class="code-text">{{ row.calc_no }}</span>
            <span v-else-if="row.session_id" class="text-muted" style="font-size:11px" :title="row.session_id">
              {{ row.session_id.slice(0, 8) }}…
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="error_code" label="错误码" width="120">
          <template #default="{ row }">{{ row.error_code || '—' }}</template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.error_msg || '—' }}</template>
        </el-table-column>
        <el-table-column label="耗时(ms)" width="90">
          <template #default="{ row }">
            <span v-if="row.duration_ms != null" :style="{ color: row.duration_ms > 30000 ? '#f85149' : 'inherit' }">
              {{ row.duration_ms }}
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="超时范围" width="90" align="center">
          <template #default="{ row }">
            <template v-if="row.anomaly_type === 'calc_timeout'">
              <el-tag v-if="row.scope === 'session'" type="warning" size="small">session</el-tag>
              <el-tag v-else-if="row.scope === 'single'" type="danger" size="small">单方案</el-tag>
              <span v-else class="text-muted">—</span>
            </template>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="扩展信息" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-muted" style="font-size:11px">{{ row.extra || '—' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div style="display:flex;justify-content:flex-end;margin-top:12px">
        <el-pagination
          v-model:current-page="page" :page-size="pageSize" :total="total"
          layout="total, prev, pager, next" @current-change="handlePageChange"
          background small
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getAnomalyStats, getAnomalyList } from '../../api/anomaly.js'

// ECharts 实际 hex 颜色（不能用 CSS 变量）
const CHART_COLORS = { ai_failure: '#f85149', calc_anomaly: '#d29922', calc_timeout: '#388bfd' }
const CHART_TEXT   = '#8b949e'
const CHART_SPLIT  = '#21262d'

// ── KPI ───────────────────────────────────────────────────────────────────────
const kpiCards = ref([
  { label: 'AI 调用失败',  badge: '近7天', badgeBg: 'rgba(248,81,73,.12)',   color: 'var(--red)',    value: '—', sub: '包含重试耗尽 & agent 崩溃' },
  { label: '计算结果异常', badge: '近7天', badgeBg: 'rgba(210,153,34,.12)',  color: 'var(--amber)',  value: '—', sub: '装不下 / 利用率 <30%' },
  { label: '计算超时',     badge: '近7天', badgeBg: 'rgba(56,139,253,.12)', color: 'var(--blue)',   value: '—', sub: '单方案超时 >30s（不含 session 汇总）' },
  { label: '今日异常合计', badge: '今日',  badgeBg: 'rgba(163,113,247,.12)', color: 'var(--purple)', value: '—', sub: '所有类型累计' },
])

// ── 趋势图 ────────────────────────────────────────────────────────────────────
const trendChart = ref(null)
let chartInst = null
const days = ref(7)

// ── 明细列表 ──────────────────────────────────────────────────────────────────
const listRows    = ref([])
const listLoading = ref(false)
const total       = ref(0)
const page        = ref(1)
const pageSize    = 20

const filter = reactive({
  anomaly_type: '',
  severity:     '',
  dateRange:    [],
})

// ── 工具函数 ──────────────────────────────────────────────────────────────────
const TYPE_LABELS = { ai_failure: 'AI调用失败', calc_anomaly: '计算异常', calc_timeout: '计算超时' }
const typeLabel       = t => TYPE_LABELS[t] || t
const typeTagType     = t => ({ ai_failure: 'danger', calc_anomaly: 'warning', calc_timeout: 'primary' }[t] || 'info')
const severityTagType = s => ({ critical: 'danger', error: 'warning', warning: 'info' }[s] || 'info')

// ── 数据加载 ──────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const { data } = await getAnomalyStats(days.value)
    const byCnt = {}
    for (const r of data.by_type) {
      byCnt[r.anomaly_type] = (byCnt[r.anomaly_type] || 0) + r.cnt
    }
    kpiCards.value[0].value = byCnt['ai_failure']  ?? 0
    kpiCards.value[1].value = byCnt['calc_anomaly'] ?? 0
    kpiCards.value[2].value = byCnt['calc_timeout'] ?? 0
    kpiCards.value[3].value = data.today ?? 0
    renderTrend(data.trend)
  } catch (e) {
    console.error(e)
  }
}

async function loadList() {
  listLoading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (filter.anomaly_type) params.anomaly_type = filter.anomaly_type
    if (filter.severity)     params.severity     = filter.severity
    if (filter.dateRange?.length === 2) {
      params.date_start = filter.dateRange[0]
      params.date_end   = filter.dateRange[1]
    }
    const { data } = await getAnomalyList(params)
    listRows.value = data.rows
    total.value    = data.total
  } catch (e) {
    console.error(e)
  } finally {
    listLoading.value = false
  }
}

function handleQuery() {
  page.value = 1
  loadList()
}

function handlePageChange() {
  loadList()
}

function resetFilter() {
  filter.anomaly_type = ''
  filter.severity     = ''
  filter.dateRange    = []
  page.value          = 1
  loadList()
}

async function changeDays(d) {
  days.value = d
  const label = d === 7 ? '近7天' : d === 14 ? '近14天' : '近30天'
  kpiCards.value.forEach((c, i) => { c.badge = i === 3 ? '今日' : label })
  await loadStats()
}

// ── 趋势图渲染 ────────────────────────────────────────────────────────────────
function renderTrend(trendData) {
  if (!chartInst) return
  const daySet = [...new Set(trendData.map(r => r.day))].sort()
  const types  = ['ai_failure', 'calc_anomaly', 'calc_timeout']
  const labels = ['AI调用失败', '计算异常', '计算超时']
  const seriesMap = {}
  for (const r of trendData) {
    if (!seriesMap[r.anomaly_type]) seriesMap[r.anomaly_type] = {}
    seriesMap[r.anomaly_type][r.day] = r.cnt
  }
  const series = types.map((t, i) => ({
    name:        labels[i],
    type:        'bar',
    stack:       'total',
    data:        daySet.map(d => seriesMap[t]?.[d] ?? 0),
    itemStyle:   { color: CHART_COLORS[t] },
    barMaxWidth: 32,
  }))
  chartInst.setOption({
    backgroundColor: 'transparent',
    tooltip:  { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend:   { top: 0, right: 0, textStyle: { color: CHART_TEXT, fontSize: 11 } },
    grid:     { top: 36, right: 16, bottom: 24, left: 40 },
    xAxis: {
      type: 'category', data: daySet,
      axisLabel: { color: CHART_TEXT, fontSize: 11 },
      axisLine:  { lineStyle: { color: CHART_SPLIT } },
      axisTick:  { show: false },
    },
    yAxis: {
      type: 'value', minInterval: 1,
      axisLabel: { color: CHART_TEXT, fontSize: 11 },
      splitLine: { lineStyle: { color: CHART_SPLIT, type: 'dashed' } },
    },
    series,
  }, true)
}

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  await nextTick()
  chartInst = echarts.init(trendChart.value)
  await loadStats()
  await loadList()
  window.addEventListener('resize', () => chartInst?.resize())
})

onUnmounted(() => {
  chartInst?.dispose()
  window.removeEventListener('resize', () => chartInst?.resize())
})
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.kpi-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  transition: border-color .2s;
  box-shadow: var(--shadow);
}
.kpi-card:hover { border-color: var(--border-hover); }
.kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.kpi-label  { font-size: 11px; font-weight: 600; letter-spacing: .5px; color: var(--text-secondary); text-transform: uppercase; }
.kpi-badge  { font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 10px; }
.kpi-value  { font-size: 28px; font-weight: 700; line-height: 1; margin-bottom: 6px; font-variant-numeric: tabular-nums; }
.kpi-sub    { font-size: 11px; color: var(--text-muted); }
.text-muted { color: var(--text-muted); }
.code-text  { font-family: monospace; font-size: 12px; color: var(--blue); }

/* 修复 El-Plus stripe 在暗色主题下条纹行文字不可见的问题 */
.anomaly-table :deep(.el-table__row--striped td.el-table__cell) {
  background: rgba(255,255,255,0.025) !important;
  color: var(--text-primary) !important;
}
.anomaly-table :deep(td.el-table__cell) {
  color: var(--text-primary) !important;
}
</style>
