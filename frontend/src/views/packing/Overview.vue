<template>
  <div>
    <!-- Row 1：业务核心 KPI -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="card in cards" :key="card.label">
        <div class="kpi-header">
          <span class="kpi-label">{{ card.label }}</span>
          <span class="kpi-badge" :style="{ background: card.badgeBg, color: card.color }">{{ card.badge }}</span>
        </div>
        <div class="kpi-value" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="kpi-sub">
          {{ card.sub }}
          <span v-if="card.wow != null" class="wow-badge" :class="card.wow >= 0 ? 'wow-up' : 'wow-down'">
            {{ card.wow >= 0 ? '↑' : '↓' }}{{ Math.abs(card.wow) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Row 2：AI 成本 KPI（装箱推荐 + 防护分析 两种场景，5列） -->
    <div class="kpi-row" style="margin-top:0;grid-template-columns:repeat(5,1fr)">
      <div class="kpi-card" v-for="card in aiCards" :key="card.label">
        <div class="kpi-header">
          <span class="kpi-label">{{ card.label }}</span>
          <span class="kpi-badge" :style="{ background: card.badgeBg, color: card.color }">{{ card.badge }}</span>
        </div>
        <div class="kpi-value" :style="{ color: card.color, fontSize: '22px' }">{{ card.value }}</div>
        <div class="kpi-sub">{{ card.sub }}</div>
      </div>
    </div>

    <!-- 图表区：时间范围切换 -->
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px">
      <el-button-group size="small">
        <el-button :type="trendDays===7 ?'primary':''" @click="changeDays(7)">近 7 天</el-button>
        <el-button :type="trendDays===30?'primary':''" @click="changeDays(30)">近 30 天</el-button>
        <el-button :type="trendDays===90?'primary':''" @click="changeDays(90)">近 90 天</el-button>
      </el-button-group>
    </div>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never" header="每日计算次数趋势">
          <div ref="trendChart" style="height:280px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" header="推荐方案类型分布">
          <div ref="pieChart" style="height:280px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getOverview, getDailyTrend, getWinnerDist } from '../../api/packing.js'
import { theme, isDark } from '../../theme.js'
import { getChartTheme, PALETTE } from '../../chartTheme.js'

// ── KPI 数据 ──────────────────────────────────────────────────────────────────

const cards = ref([
  { label: '累计计算次数', value: '—', sub: '—', badge: 'TOTAL',  color: '#388bfd', badgeBg: 'rgba(56,139,253,.12)',  wow: null },
  { label: 'AI 驱动占比',  value: '—', sub: '—', badge: 'AI',     color: '#a371f7', badgeBg: 'rgba(163,113,247,.12)', wow: null },
  { label: '推荐采纳率',   value: '—', sub: '—', badge: 'ADOPT',  color: '#3fb950', badgeBg: 'rgba(63,185,80,.12)',   wow: null },
  { label: '实际节省费用', value: '—', sub: '—', badge: 'SAVING', color: '#d29922', badgeBg: 'rgba(210,153,34,.12)',  wow: null },
])

const aiCards = ref([
  { label: '累计输入 Token', value: '—', sub: '—', badge: 'INPUT',  color: '#39c5cf', badgeBg: 'rgba(57,197,207,.12)' },
  { label: '累计输出 Token', value: '—', sub: '—', badge: 'OUTPUT', color: '#388bfd', badgeBg: 'rgba(56,139,253,.12)' },
  { label: '装箱推荐 AI 成本', value: '—', sub: '主 Agent 多轮对话消耗', badge: '装箱', color: '#f85149', badgeBg: 'rgba(248,81,73,.12)' },
  { label: '防护分析 AI 成本', value: '—', sub: '防护等级分类调用消耗', badge: '分类', color: '#d29922', badgeBg: 'rgba(210,153,34,.12)' },
  { label: 'AI ROI', value: '—', sub: '实际节省 / AI 成本（基于反馈记录）', badge: 'ROI', color: '#3fb950', badgeBg: 'rgba(63,185,80,.12)' },
])

function fmtK(n) {
  if (!n) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

// ── 图表 ──────────────────────────────────────────────────────────────────────

const trendChart = ref(null)
const pieChart   = ref(null)
const trendDays  = ref(30)

let tcInst = null
let pcInst = null
let cachedTrend = []
let cachedDist  = []

const grad = (c0, c1) => new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: c0 }, { offset: 1, color: c1 }])

function applyTrendOption(dark) {
  const { TT, AXIS } = getChartTheme(dark)
  tcInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'axis' },
    legend: {
      data: ['总计算次数', 'AI 决策次数'],
      textStyle: { color: AXIS.axisLabel.color, fontSize: 12 },
      itemWidth: 12, itemHeight: 8, bottom: 0,
    },
    grid: { top: 24, bottom: 46, left: 44, right: 16 },
    xAxis: { type: 'category', data: cachedTrend.map(r => r.date), ...AXIS },
    yAxis: { type: 'value', minInterval: 1, ...AXIS },
    series: [
      {
        name: '总计算次数', type: 'bar', barMaxWidth: 28,
        data: cachedTrend.map(r => r.total),
        itemStyle: { color: grad('#388bfd', 'rgba(56,139,253,.12)'), borderRadius: [3,3,0,0] },
      },
      {
        name: 'AI 决策次数', type: 'line', smooth: true,
        data: cachedTrend.map(r => r.ai_count),
        symbol: 'circle', symbolSize: 4,
        lineStyle: { color: '#3fb950', width: 2 },
        itemStyle: { color: '#3fb950' },
        areaStyle: { color: grad('rgba(63,185,80,.2)', 'rgba(63,185,80,0)') },
      },
    ],
  }, true)
}

function applyPieOption(dark) {
  const { TT, legendText } = getChartTheme(dark)
  const nameMap = { rec: '推荐新包材', soft: '软包材', best: '包材库最优', '推荐新包材': '推荐新包材', '软包材': '软包材' }
  pcInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'item', formatter: '{b}<br/>数量：{c}（{d}%）' },
    legend: { bottom: 0, textStyle: legendText, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '46%'],
      data: cachedDist.map((r, i) => ({
        name: nameMap[r.winner] || r.winner, value: r.count,
        itemStyle: { color: PALETTE[i % PALETTE.length] },
      })),
      label: { show: false },
      emphasis: { scale: true, scaleSize: 4 },
    }],
  }, true)
}

async function changeDays(d) {
  trendDays.value = d
  cachedTrend = await getDailyTrend(d).then(r => r.data)
  applyTrendOption(isDark())
}

// ── 挂载 ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  const [ov, trend, dist] = await Promise.all([
    getOverview().then(r => r.data),
    getDailyTrend(trendDays.value).then(r => r.data),
    getWinnerDist().then(r => r.data),
  ])

  // Row 1：业务 KPI
  cards.value = [
    {
      label: '累计计算次数', value: ov.total_calcs,
      sub: `本周 ${ov.this_week_calcs} 次 | 上周 ${ov.last_week_calcs} 次`,
      badge: 'TOTAL', color: '#388bfd', badgeBg: 'rgba(56,139,253,.12)',
      wow: ov.calcs_wow,
    },
    {
      label: 'AI 驱动占比', value: ov.ai_rate + '%',
      sub: `共 ${ov.ai_calcs} 次 AI 决策，降级 ${ov.ai_fallback_count} 次`,
      badge: 'AI', color: '#a371f7', badgeBg: 'rgba(163,113,247,.12)',
      wow: null,
    },
    {
      label: '推荐采纳率', value: ov.adoption_rate + '%',
      sub: `${ov.adopted_count} / ${ov.total_feedback}（基于有反馈记录）`,
      badge: 'ADOPT', color: '#3fb950', badgeBg: 'rgba(63,185,80,.12)',
      wow: null,
    },
    {
      label: '实际节省费用', value: '$' + (ov.actual_fee_saved || 0).toFixed(2),
      sub: `理论上限 $${ov.total_fee_saved}（近7天 +$${ov.this_week_saving}）`,
      badge: 'SAVING', color: '#d29922', badgeBg: 'rgba(210,153,34,.12)',
      wow: ov.saving_wow,
    },
  ]

  // Row 2：AI 成本（装箱推荐 + 防护分析两种场景）
  const totalIn  = ov.total_input_tokens  || 0
  const totalOut = ov.total_output_tokens || 0
  const clsIn    = ov.classify_input_tokens  || 0
  const clsOut   = ov.classify_output_tokens || 0
  aiCards.value = [
    {
      label: '累计输入 Token', value: fmtK(totalIn + clsIn),
      sub: `装箱推荐 ${totalIn.toLocaleString()} + 防护分析 ${clsIn.toLocaleString()}`,
      badge: 'INPUT', color: '#39c5cf', badgeBg: 'rgba(57,197,207,.12)',
    },
    {
      label: '累计输出 Token', value: fmtK(totalOut + clsOut),
      sub: `装箱推荐 ${totalOut.toLocaleString()} + 防护分析 ${clsOut.toLocaleString()}`,
      badge: 'OUTPUT', color: '#388bfd', badgeBg: 'rgba(56,139,253,.12)',
    },
    {
      label: '装箱推荐 AI 成本', value: '$' + (ov.ai_cost_usd || 0).toFixed(4),
      sub: `输入 ${totalIn.toLocaleString()} / 输出 ${totalOut.toLocaleString()} tokens`,
      badge: '装箱', color: '#f85149', badgeBg: 'rgba(248,81,73,.12)',
    },
    {
      label: '防护分析 AI 成本', value: '$' + (ov.classify_cost_usd || 0).toFixed(4),
      sub: `输入 ${clsIn.toLocaleString()} / 输出 ${clsOut.toLocaleString()} tokens`,
      badge: '分类', color: '#d29922', badgeBg: 'rgba(210,153,34,.12)',
    },
    {
      label: 'AI ROI',
      value: ov.ai_roi != null ? ov.ai_roi + '×' : '数据不足',
      sub: '实际节省 / AI 成本（基于反馈记录）',
      badge: 'ROI', color: '#3fb950', badgeBg: 'rgba(63,185,80,.12)',
    },
  ]

  cachedTrend = trend
  cachedDist  = dist

  tcInst = echarts.init(trendChart.value)
  pcInst = echarts.init(pieChart.value)

  applyTrendOption(isDark())
  applyPieOption(isDark())
})

watch(theme, val => {
  const dark = val === 'dark'
  if (tcInst) applyTrendOption(dark)
  if (pcInst) applyPieOption(dark)
})
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.kpi-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  transition: border-color .2s;
}
.kpi-card:hover { border-color: var(--border-hover); }

.kpi-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}
.kpi-label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.kpi-badge {
  font-size: 9px; font-weight: 700; letter-spacing: .8px;
  padding: 2px 6px; border-radius: 4px;
}
.kpi-value {
  font-size: 28px; font-weight: 700; line-height: 1;
  margin-bottom: 8px; font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}
.kpi-sub { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }

.wow-badge {
  font-size: 10px; font-weight: 600;
  padding: 1px 5px; border-radius: 3px;
  white-space: nowrap;
}
.wow-up   { color: #3fb950; background: rgba(63,185,80,.12); }
.wow-down { color: #f85149; background: rgba(248,81,73,.12); }
</style>
