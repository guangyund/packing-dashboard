<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="16">
        <el-card shadow="never" header="每日节省 FBA 费用趋势（USD）">
          <div ref="savingChart" style="height:256px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" header="FBA 费档分布">
          <div ref="tierChart" style="height:256px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never" header="装箱空间利用率分布">
          <div ref="utilChart" style="height:220px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" header="降档次数趋势">
          <div ref="upgradeChart" style="height:220px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="24">
        <el-card shadow="never" header="每日 AI Token 消耗趋势">
          <div ref="tokenChart" style="height:220px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ── 包材推荐分析 ────────────────────────────────────── -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="14">
        <el-card shadow="never" header="包材推荐次数 TOP 15（全量）">
          <div ref="binChart" style="height:340px"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" header="产品分类节省费用对比（全量）">
          <div ref="categoryChart" style="height:340px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getBenefit } from '../../api/packing.js'
import { theme, isDark } from '../../theme.js'
import { getChartTheme, PALETTE } from '../../chartTheme.js'

const savingChart   = ref(null)
const tierChart     = ref(null)
const utilChart     = ref(null)
const upgradeChart  = ref(null)
const tokenChart    = ref(null)
const binChart      = ref(null)
const categoryChart = ref(null)

const grad = (c0, c1) => new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: c0 }, { offset: 1, color: c1 }])
const gradH = (c0, c1) => new echarts.graphic.LinearGradient(1, 0, 0, 0, [{ offset: 0, color: c0 }, { offset: 1, color: c1 }])
const GRID    = { top: 20, bottom: 36, left: 52, right: 16 }
const GRID_SM = { top: 16, bottom: 32, left: 44, right: 12 }

let savingInst   = null
let tierInst     = null
let utilInst     = null
let upgradeInst  = null
let tokenInst    = null
let binInst      = null
let categoryInst = null
let cachedData   = null

const truncate = (s, n = 18) => s && s.length > n ? s.slice(0, n) + '…' : (s || '')

function applyAll(dark) {
  const { TT, AXIS, legendText } = getChartTheme(dark)
  const data  = cachedData
  const dates = data.daily_saving.map(r => r.date)

  const xCat = (d) => ({ type: 'category', data: d, ...AXIS })
  const yCat = (d) => ({ type: 'category', data: d, ...AXIS, axisLabel: { ...AXIS.axisLabel, width: 120, overflow: 'truncate' } })
  const yVal = (fmt) => ({
    type: 'value',
    axisLabel: { formatter: fmt || (v => v), color: AXIS.axisLabel.color, fontSize: 11 },
    splitLine: AXIS.splitLine,
  })
  const xVal = (fmt) => ({
    type: 'value',
    axisLabel: { formatter: fmt || (v => v), color: AXIS.axisLabel.color, fontSize: 11 },
    splitLine: AXIS.splitLine,
  })

  // ── 每日节省趋势 ──
  savingInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'axis', formatter: p => `${p[0].axisValue}<br/>节省：<b style="color:#3fb950">$${p[0].value}</b>` },
    grid: GRID,
    xAxis: xCat(dates),
    yAxis: yVal(v => '$' + v),
    series: [{
      type: 'bar', barMaxWidth: 28,
      data: data.daily_saving.map(r => r.saved),
      itemStyle: { color: grad('#3fb950', 'rgba(63,185,80,.08)'), borderRadius: [3,3,0,0] },
    }],
  }, true)

  // ── 费档分布 ──
  tierInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'item', formatter: '{b}<br/>数量：{c}（{d}%）' },
    legend: { bottom: 0, textStyle: legendText, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie', radius: ['36%', '60%'], center: ['50%', '44%'],
      data: data.tier_distribution.map((r, i) => ({
        name: r.winner_tier, value: r.cnt,
        itemStyle: { color: PALETTE[i % PALETTE.length] },
      })),
      label: { show: false },
      emphasis: { scale: true, scaleSize: 4 },
    }],
  }, true)

  // ── 利用率分布 ──
  utilInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'axis' },
    grid: GRID_SM,
    xAxis: xCat(data.utilization_dist.map(r => r.range_label)),
    yAxis: yVal(),
    series: [{
      type: 'bar', barMaxWidth: 52,
      data: data.utilization_dist.map(r => r.cnt),
      itemStyle: { color: grad('#388bfd', 'rgba(56,139,253,.08)'), borderRadius: [4,4,0,0] },
    }],
  }, true)

  // ── 降档趋势 ──
  upgradeInst.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...TT, trigger: 'axis' },
    grid: GRID_SM,
    xAxis: xCat(dates),
    yAxis: yVal(),
    series: [{
      type: 'line', smooth: true,
      data: data.daily_saving.map(r => r.upgraded),
      symbol: 'circle', symbolSize: 4,
      lineStyle: { color: '#a371f7', width: 2 },
      itemStyle: { color: '#a371f7' },
      areaStyle: { color: grad('rgba(163,113,247,.2)', 'rgba(163,113,247,0)') },
    }],
  }, true)

  // ── Token 趋势 ──
  const tkDates = (data.token_daily || []).map(r => r.date)
  tokenInst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TT, trigger: 'axis',
      formatter: p => `${p[0].axisValue}<br/>`
        + p.map(s => `${s.marker}${s.seriesName}：<b>${s.value?.toLocaleString()}</b>`).join('<br/>'),
    },
    legend: { data: ['输入 Token', '输出 Token'], textStyle: legendText, bottom: 0, itemWidth: 12, itemHeight: 8 },
    grid: { top: 24, bottom: 46, left: 60, right: 16 },
    xAxis: xCat(tkDates),
    yAxis: yVal(v => v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v),
    series: [
      {
        name: '输入 Token', type: 'bar', stack: 'token', barMaxWidth: 28,
        data: (data.token_daily || []).map(r => r.input_tokens),
        itemStyle: { color: '#39c5cf' },
      },
      {
        name: '输出 Token', type: 'bar', stack: 'token', barMaxWidth: 28,
        data: (data.token_daily || []).map(r => r.output_tokens),
        itemStyle: { color: '#388bfd', borderRadius: [3,3,0,0] },
      },
    ],
  }, true)

  // ── 包材推荐分析（横向柱状，倒序让最多的在顶部）──
  const bins = [...(data.bin_stats || [])].reverse()
  const binNames    = bins.map(r => truncate(r.bin))
  const binCounts   = bins.map(r => r.rec_count)
  const binAdoption = bins.map(r => r.adoption_rate)
  binInst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TT, trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const idx = bins.length - 1 - params[0].dataIndex
        const r = bins[params[0].dataIndex]
        const adopt = r.adoption_rate != null ? r.adoption_rate + '%' : '无反馈'
        return `${r.bin}<br/>推荐次数：<b>${r.rec_count}</b><br/>采纳率：<b>${adopt}</b><br/>理论节省：<b>$${r.theory_saving}</b>`
      },
    },
    grid: { top: 12, bottom: 12, left: 140, right: 60, containLabel: false },
    xAxis: xVal(),
    yAxis: { type: 'category', data: binNames, ...AXIS,
      axisLabel: { ...AXIS.axisLabel, fontSize: 11, width: 128, overflow: 'truncate' } },
    series: [{
      type: 'bar', barMaxWidth: 18,
      data: binCounts,
      itemStyle: { color: gradH('#388bfd', 'rgba(56,139,253,.25)'), borderRadius: [0,4,4,0] },
      label: {
        show: true, position: 'right', fontSize: 11,
        color: AXIS.axisLabel.color,
        formatter: (p) => {
          const r = bins[p.dataIndex]
          return r.adoption_rate != null ? r.adoption_rate + '%' : ''
        },
      },
    }],
  }, true)

  // ── 产品分类节省对比 ──
  const cats = [...(data.category_stats || [])].reverse()
  const catNames   = cats.map(r => r.category)
  const catSavings = cats.map(r => r.theory_saving)
  categoryInst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TT, trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const r = cats[params[0].dataIndex]
        return `${r.category}<br/>理论节省：<b>$${r.theory_saving}</b><br/>计算次数：<b>${r.calc_count}</b><br/>平均利用率：<b>${r.avg_utilization}%</b>`
      },
    },
    grid: { top: 12, bottom: 12, left: 100, right: 50, containLabel: false },
    xAxis: xVal(v => '$' + v),
    yAxis: { type: 'category', data: catNames, ...AXIS,
      axisLabel: { ...AXIS.axisLabel, fontSize: 11 } },
    series: [{
      type: 'bar', barMaxWidth: 20,
      data: catSavings,
      itemStyle: { color: gradH('#d29922', 'rgba(210,153,34,.25)'), borderRadius: [0,4,4,0] },
      label: {
        show: true, position: 'right', fontSize: 11,
        color: AXIS.axisLabel.color,
        formatter: p => p.value > 0 ? '$' + p.value : '',
      },
    }],
  }, true)
}

onMounted(async () => {
  cachedData = await getBenefit(30).then(r => r.data)

  savingInst   = echarts.init(savingChart.value)
  tierInst     = echarts.init(tierChart.value)
  utilInst     = echarts.init(utilChart.value)
  upgradeInst  = echarts.init(upgradeChart.value)
  tokenInst    = echarts.init(tokenChart.value)
  binInst      = echarts.init(binChart.value)
  categoryInst = echarts.init(categoryChart.value)

  applyAll(isDark())
})

watch(theme, val => {
  if (cachedData) applyAll(val === 'dark')
})
</script>
