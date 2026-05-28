/**
 * 根据当前主题返回 ECharts 公共配置项
 * isDark: boolean
 */
export function getChartTheme(isDark) {
  const TT = {
    backgroundColor: isDark ? 'rgba(22,27,34,0.96)' : 'rgba(255,255,255,0.98)',
    borderColor:     isDark ? 'rgba(240,246,252,0.12)' : 'rgba(15,23,42,0.1)',
    borderWidth: 1,
    padding: [8, 12],
    textStyle: { color: isDark ? '#e6edf3' : '#1e293b', fontSize: 12 },
    extraCssText: `border-radius:6px;box-shadow:0 8px 20px rgba(0,0,0,${isDark ? '.5' : '.12'})`,
  }

  const AXIS = {
    axisLine:  { lineStyle: { color: isDark ? '#30363d' : 'rgba(0,0,0,0.1)' } },
    axisTick:  { show: false },
    axisLabel: { color: isDark ? '#8b949e' : '#6b7280', fontSize: 11 },
    splitLine: { lineStyle: { color: isDark ? '#21262d' : 'rgba(0,0,0,0.06)', type: 'dashed' } },
  }

  const legendText = { color: isDark ? '#8b949e' : '#6b7280', fontSize: 12 }

  return { TT, AXIS, legendText }
}

export const PALETTE = ['#388bfd', '#3fb950', '#a371f7', '#d29922', '#39c5cf', '#f85149']
