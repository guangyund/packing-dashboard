<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="12">
        <el-card shadow="never" header="按方案类型的采纳率">
          <div ref="planChart" style="height:256px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" header="按选择方式的采纳率">
          <div ref="methodChart" style="height:256px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" header="未采纳推荐 TOP 原因">
      <el-table :data="reasons" style="width:100%" size="small">
        <el-table-column prop="reason_changed" label="未采纳原因" />
        <el-table-column prop="cnt" label="次数" width="100" align="center" />
      </el-table>
      <el-empty v-if="reasons.length === 0" description="暂无数据" :image-size="56" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getAdoptionAnalysis } from '../../api/packing.js'
import { theme, isDark } from '../../theme.js'
import { getChartTheme } from '../../chartTheme.js'

const planChart   = ref(null)
const methodChart = ref(null)
const reasons     = ref([])

const planLabel   = { rec: '推荐新包材', soft: '软包材', best: '包材库最优' }
const methodLabel = { default: '系统默认', auto: '静默自动', manual: '手动选择' }

const barColor = r => r >= 70 ? '#3fb950' : r >= 40 ? '#d29922' : '#f85149'

let planInst   = null
let methodInst = null
let cachedPlan   = []
let cachedMethod = []

function buildBarOption(dark, rows, labelMap) {
  const { TT, AXIS } = getChartTheme(dark)
  const labels = rows.map(r => labelMap[r.selected_plan || r.selection_method] || r.selected_plan || r.selection_method)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      ...TT, trigger: 'axis',
      formatter: p => {
        const row = rows.find(r => (labelMap[r.selected_plan || r.selection_method] || r.selected_plan || r.selection_method) === p[0].name)
        return `${p[0].name}<br/>采纳率：<b style="color:${barColor(p[0].value)}">${p[0].value}%</b><br/>样本量：${row?.total ?? '—'}`
      },
    },
    grid: { top: 20, bottom: 28, left: 48, right: 16 },
    xAxis: { type: 'category', data: labels, ...AXIS },
    yAxis: {
      type: 'value', max: 100,
      axisLabel: { formatter: '{value}%', color: AXIS.axisLabel.color, fontSize: 11 },
      splitLine: AXIS.splitLine,
    },
    series: [{
      type: 'bar', barMaxWidth: 56,
      data: rows.map(r => ({
        value: r.rate,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: barColor(r.rate) },
            { offset: 1, color: barColor(r.rate) + '1a' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      })),
      label: { show: true, position: 'top', formatter: '{c}%', color: AXIS.axisLabel.color, fontSize: 11 },
    }],
  }
}

onMounted(async () => {
  const data = await getAdoptionAnalysis().then(r => r.data)
  reasons.value = data.top_reasons
  cachedPlan   = data.by_plan
  cachedMethod = data.by_method

  planInst   = echarts.init(planChart.value)
  methodInst = echarts.init(methodChart.value)

  planInst.setOption(buildBarOption(isDark(), cachedPlan, planLabel))
  methodInst.setOption(buildBarOption(isDark(), cachedMethod, methodLabel))
})

watch(theme, val => {
  const dark = val === 'dark'
  if (planInst)   planInst.setOption(buildBarOption(dark, cachedPlan, planLabel), true)
  if (methodInst) methodInst.setOption(buildBarOption(dark, cachedMethod, methodLabel), true)
})
</script>
