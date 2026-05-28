<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark"><span>D</span></div>
        <div>
          <div class="logo-title">数据中控平台</div>
          <div class="logo-sub">Analytics Center</div>
        </div>
      </div>

      <div class="nav-section-label">包装推荐系统</div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems" :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-dot" :class="{ active: $route.path === item.path }"></span>
          {{ item.label }}
        </router-link>
      </nav>

      <div class="sidebar-status">
        <span class="status-indicator"></span>
        数据服务运行中
      </div>
    </aside>

    <div class="body">
      <header class="topbar">
        <span class="topbar-title">{{ $route.meta?.title }}</span>
        <div class="topbar-right">
          <!-- 主题切换 -->
          <div class="theme-switcher">
            <button
              class="theme-btn"
              :class="{ active: currentTheme === 'dark' }"
              @click="setTheme('dark')"
            >科技</button>
            <button
              class="theme-btn"
              :class="{ active: currentTheme === 'light' }"
              @click="setTheme('light')"
            >简约</button>
          </div>
          <span class="topbar-clock">{{ clock }}</span>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { theme } from './theme.js'

const currentTheme = theme
const setTheme = val => { theme.value = val }

const clock = ref('')
let timer = null
const tick = () => { clock.value = new Date().toLocaleString('zh-CN', { hour12: false }) }
onMounted(() => { tick(); timer = setInterval(tick, 1000) })
onUnmounted(() => clearInterval(timer))

const navItems = [
  { path: '/packing/overview', label: '使用概览'  },
  { path: '/packing/adoption', label: '采纳率分析' },
  { path: '/packing/benefit',  label: '效益量化'  },
  { path: '/packing/detail',   label: '明细查询'  },
  { path: '/packing/anomaly',  label: '异常监控'  },
]
</script>

<style>
/* ═══════════════════════════════════════════════════════
   Reset
════════════════════════════════════════════════════════ */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
body { font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif; }

/* ═══════════════════════════════════════════════════════
   科技风（暗色）Token — 默认 / data-theme="dark"
════════════════════════════════════════════════════════ */
:root,
[data-theme="dark"] {
  --bg-base:       #0d1117;
  --bg-raised:     #161b22;
  --bg-overlay:    #1c2128;
  --blue:          #388bfd;
  --blue-subtle:   rgba(56,139,253,.10);
  --blue-muted:    rgba(56,139,253,.25);
  --green:         #3fb950;
  --amber:         #d29922;
  --red:           #f85149;
  --purple:        #a371f7;
  --teal:          #39c5cf;
  --border:        #30363d;
  --border-hover:  #3d444d;
  --border-active: rgba(56,139,253,.40);
  --text-primary:  #e6edf3;
  --text-secondary:#8b949e;
  --text-muted:    #484f58;
  --shadow:        none;
}

/* 用 html[data-theme="dark"]（优先级 0,1,1）覆盖 El Plus 的 :root（0,1,0）变量，
   确保不被 El Plus 后加载的 CSS 覆回白色 */
html[data-theme="dark"] {
  --el-border-color:              #30363d;
  --el-border-color-light:        #30363d;
  --el-border-color-lighter:      #30363d;
  --el-border-color-extra-light:  #30363d;
  --el-fill-color-blank:          #0d1117;
  --el-fill-color:                #1c2128;
  --el-bg-color:                  #161b22;
  --el-bg-color-overlay:          #1c2128;
  --el-bg-color-page:             #0d1117;
  --el-text-color-primary:        #e6edf3;
  --el-text-color-regular:        #8b949e;
  --el-text-color-secondary:      #8b949e;
  --el-text-color-placeholder:    #484f58;
  --el-table-border-color:        #30363d;
  --el-table-bg-color:            transparent;
  --el-table-tr-bg-color:         transparent;
  --el-table-header-bg-color:     #1c2128;
  --el-table-row-hover-bg-color:  #1c2128;
}

/* ═══════════════════════════════════════════════════════
   简约风（亮色）Token — data-theme="light"
════════════════════════════════════════════════════════ */
[data-theme="light"] {
  --bg-base:       #f1f5f9;
  --bg-raised:     #ffffff;
  --bg-overlay:    #f8fafc;
  --blue:          #3b82f6;
  --blue-subtle:   rgba(59,130,246,.08);
  --blue-muted:    rgba(59,130,246,.28);
  --green:         #16a34a;
  --amber:         #ca8a04;
  --red:           #dc2626;
  --purple:        #7c3aed;
  --teal:          #0891b2;
  --border:        rgba(15,23,42,.09);
  --border-hover:  rgba(15,23,42,.22);
  --border-active: rgba(59,130,246,.40);
  --text-primary:  #0f172a;
  --text-secondary:#475569;
  --text-muted:    #94a3b8;
  --shadow:        0 1px 4px rgba(15,23,42,.08);

}

html[data-theme="light"] {
  --el-border-color:              rgba(15,23,42,.12);
  --el-border-color-light:        rgba(15,23,42,.09);
  --el-border-color-lighter:      rgba(15,23,42,.07);
  --el-fill-color-blank:          #ffffff;
  --el-fill-color:                #f8fafc;
  --el-bg-color:                  #ffffff;
  --el-bg-color-overlay:          #ffffff;
  --el-bg-color-page:             #f1f5f9;
  --el-text-color-primary:        #0f172a;
  --el-text-color-regular:        #475569;
  --el-text-color-secondary:      #475569;
  --el-text-color-placeholder:    #94a3b8;
  --el-table-border-color:        rgba(15,23,42,.09);
  --el-table-bg-color:            transparent;
  --el-table-tr-bg-color:         transparent;
  --el-table-header-bg-color:     #f8fafc;
  --el-table-row-hover-bg-color:  #f8fafc;
}

/* ═══════════════════════════════════════════════════════
   布局骨架（CSS变量驱动，两套主题自动适配）
════════════════════════════════════════════════════════ */
.layout {
  display: flex; height: 100vh;
  background: var(--bg-base);
  overflow: hidden;
  transition: background .25s;
}
[data-theme="dark"] .layout {
  background-image: radial-gradient(ellipse 80% 60% at 60% 40%, rgba(56,139,253,.04) 0%, transparent 70%);
}

/* ── Sidebar ────────────────────────────────────────── */
.sidebar {
  width: 220px; flex-shrink: 0;
  background: var(--bg-raised);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  transition: background .25s, border-color .25s;
  box-shadow: var(--shadow);
}
.sidebar-logo {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 16px; border-bottom: 1px solid var(--border);
}
.logo-mark {
  width: 30px; height: 30px; border-radius: 7px;
  background: var(--blue);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: #fff; flex-shrink: 0;
}
.logo-title { font-size: 13px; font-weight: 700; color: var(--text-primary); letter-spacing: .2px; }
.logo-sub   { font-size: 10px; color: var(--text-muted); margin-top: 1px; letter-spacing: .5px; }

.nav-section-label {
  font-size: 10px; letter-spacing: 1px; text-transform: uppercase;
  color: var(--text-muted); padding: 18px 16px 8px;
}
.sidebar-nav { flex: 1; padding: 0 8px; display: flex; flex-direction: column; gap: 1px; }
.nav-link {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 6px;
  text-decoration: none; font-size: 13px; font-weight: 500;
  color: var(--text-secondary);
  transition: color .15s, background .15s;
}
.nav-link:hover { color: var(--text-primary); background: var(--bg-overlay); }
.nav-link.active { color: var(--blue); background: var(--blue-subtle); }
.nav-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted); flex-shrink: 0; transition: background .15s;
}
.nav-dot.active { background: var(--blue); }
.sidebar-status {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 16px; border-top: 1px solid var(--border);
  font-size: 11px; color: var(--text-muted);
}
.status-indicator {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--green); flex-shrink: 0;
}

/* ── Topbar ─────────────────────────────────────────── */
.body { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.topbar {
  height: 50px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-raised);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow);
  transition: background .25s, border-color .25s;
}
.topbar-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-clock { font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

/* 主题切换 pill */
.theme-switcher {
  display: flex; align-items: center;
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 3px;
  gap: 2px;
}
.theme-btn {
  padding: 4px 13px; border-radius: 5px;
  border: none; background: transparent; cursor: pointer;
  font-size: 12px; font-weight: 500;
  color: var(--text-muted);
  transition: all .15s;
  font-family: inherit;
}
.theme-btn.active {
  background: var(--bg-raised);
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,.12);
}
[data-theme="dark"] .theme-btn.active { box-shadow: 0 1px 4px rgba(0,0,0,.4); }

/* ── Content ────────────────────────────────────────── */
.content { flex: 1; overflow-y: auto; padding: 20px; }
.content::-webkit-scrollbar { width: 4px; }
.content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ═══════════════════════════════════════════════════════
   Element Plus 暗色覆盖（科技风 / dark）
════════════════════════════════════════════════════════ */
.el-card {
  background: var(--bg-raised) !important; border: 1px solid var(--border) !important;
  border-radius: 8px !important; box-shadow: var(--shadow) !important;
  color: var(--text-primary) !important; transition: border-color .2s, background .25s !important;
}
.el-card:hover { border-color: var(--border-hover) !important; }
.el-card__header {
  background: transparent !important; border-bottom: 1px solid var(--border) !important;
  padding: 12px 16px !important; font-size: 11px !important; font-weight: 600 !important;
  text-transform: uppercase !important; letter-spacing: .8px !important;
  color: var(--text-secondary) !important;
}
.el-card__body { padding: 16px !important; }

.el-table, .el-table__body-wrapper,
.el-table__header-wrapper, .el-table__footer-wrapper { background: transparent !important; color: var(--text-primary) !important; }
.el-table tr { background: transparent !important; }
.el-table th.el-table__cell {
  background: var(--bg-overlay) !important; color: var(--text-secondary) !important;
  border-bottom: 1px solid var(--border) !important;
  font-size: 11px !important; font-weight: 600 !important; letter-spacing: .5px !important; text-transform: uppercase !important;
}
.el-table td.el-table__cell { border-bottom: 1px solid var(--border) !important; color: var(--text-primary) !important; font-size: 12px !important; }
.el-table--border { border: 1px solid var(--border) !important; }
.el-table--border .el-table__cell { border-right: 1px solid var(--border) !important; }
/* 覆盖 Element Plus 用伪元素渲染的表格内部分隔线 */
.el-table__inner-wrapper::before,
.el-table::before,
.el-table__fixed::before,
.el-table__fixed-right::before { background-color: var(--border) !important; }
/* El Plus 在 .el-table 元素本身定义了 --el-table-row-hover-bg-color，导致 html[data-theme] 上的覆盖无效；
   在同级选择器后加载，用源顺序赢得覆盖 */
.el-table { --el-table-row-hover-bg-color: var(--bg-overlay); }
.el-table__body tr:hover > td { background: var(--bg-overlay) !important; }
.el-table__body tr.hover-row > td { background: var(--bg-overlay) !important; }
.el-table__empty-block { background: transparent !important; }
/* fixed 首列/尾列水平滚动时背景透明修复（El Plus v2.x sticky 实现）*/
.el-table td.el-table-fixed-column--left,
.el-table td.el-table-fixed-column--right { background-color: var(--bg-raised) !important; }
.el-table th.el-table-fixed-column--left,
.el-table th.el-table-fixed-column--right { background-color: var(--bg-overlay) !important; }
.el-table tr:hover td.el-table-fixed-column--left,
.el-table tr:hover td.el-table-fixed-column--right { background-color: var(--bg-overlay) !important; }
.el-table .el-table__fixed-right-patch { background-color: var(--bg-base) !important; }
.el-table__body-wrapper::-webkit-scrollbar { height: 4px; width: 4px; }
.el-table__body-wrapper::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.el-loading-mask { background: rgba(13,17,23,.75) !important; }
.el-loading-spinner .path { stroke: var(--blue) !important; }
.el-loading-spinner .el-loading-text { color: var(--blue) !important; }

.el-form-item__label { color: var(--text-secondary) !important; font-size: 12px !important; }
.el-input__wrapper {
  background: var(--bg-base) !important; border: 1px solid var(--border) !important;
  box-shadow: none !important; border-radius: 6px !important; transition: border-color .15s !important;
}
.el-input__wrapper:hover { border-color: var(--border-hover) !important; }
.el-input__wrapper.is-focus { border-color: var(--blue) !important; box-shadow: 0 0 0 2px var(--blue-subtle) !important; }
.el-input__inner { color: var(--text-primary) !important; font-size: 13px !important; background: transparent !important; }
.el-input__inner::placeholder { color: var(--text-muted) !important; }
/* 日期区间选择器内部 input */
.el-range-input { background: transparent !important; color: var(--text-primary) !important; font-size: 12px !important; }
.el-range-input::placeholder { color: var(--text-muted) !important; }
.el-range-separator { color: var(--text-muted) !important; }
.el-date-editor.el-input__wrapper { background: var(--bg-base) !important; }

.el-select .el-input__wrapper { background: var(--bg-base) !important; }
.el-select-dropdown { border-radius: 8px !important; }
.el-select-dropdown__item { font-size: 13px !important; }

/* 日期选择器弹窗 — 用 html[data-theme="dark"] 前缀（优先级 0,1,1,0）
   永远胜过 El Plus 的 .el-picker__popper.el-popper（优先级 0,0,2,0） */
html[data-theme="dark"] .el-picker__popper,
html[data-theme="dark"] .el-picker__popper.is-pure,
html[data-theme="dark"] .el-picker__popper.is-light,
html[data-theme="dark"] .el-picker__popper.el-popper { background: #1c2128 !important; border-color: #30363d !important; }
html[data-theme="dark"] .el-picker-panel,
html[data-theme="dark"] .el-picker__popper .el-picker-panel,
html[data-theme="dark"] .el-picker__popper .el-picker-panel__body-wrapper,
html[data-theme="dark"] .el-picker__popper .el-picker-panel__body { background: #1c2128 !important; border-color: #30363d !important; color: #e6edf3 !important; }
html[data-theme="dark"] .el-picker__popper .el-date-range-picker__body,
html[data-theme="dark"] .el-picker__popper .el-date-picker__body,
html[data-theme="dark"] .el-picker__popper .el-date-range-picker__content { background: #1c2128 !important; }
/* select / 通用 popper 弹窗 */
html[data-theme="dark"] .el-popper,
html[data-theme="dark"] .el-select-dropdown,
html[data-theme="dark"] .el-popper.is-light { background: #1c2128 !important; border-color: #30363d !important; color: #e6edf3 !important; }
html[data-theme="dark"] .el-popper__arrow::before { background: #1c2128 !important; border-color: #30363d !important; }
/* 覆盖 scrollbar 容器，防止其白色背景在鼠标移出选项时透出 */
html[data-theme="dark"] .el-select-dropdown .el-scrollbar,
html[data-theme="dark"] .el-select-dropdown .el-scrollbar__wrap,
html[data-theme="dark"] .el-select-dropdown .el-scrollbar__view,
html[data-theme="dark"] .el-select-dropdown__list { background: #1c2128 !important; }
/* 选项默认态（非悬停）也要显式设置背景，否则鼠标移出后会漏出白色 */
html[data-theme="dark"] .el-select-dropdown__item { background: #1c2128 !important; color: #e6edf3 !important; }
html[data-theme="dark"] .el-select-dropdown__item:hover,
html[data-theme="dark"] .el-select-dropdown__item.hover { background: #21262d !important; }
html[data-theme="dark"] .el-select-dropdown__item.selected,
html[data-theme="dark"] .el-select-dropdown__item.is-selected { color: #388bfd !important; background: rgba(56,139,253,.10) !important; }
.el-date-range-picker__header, .el-date-picker__header { color: var(--text-primary) !important; }
.el-picker-panel__icon-btn { color: var(--text-secondary) !important; }
.el-picker-panel__icon-btn:hover { color: var(--text-primary) !important; }
.el-date-table th { color: var(--text-muted) !important; border-color: var(--border) !important; }
.el-date-table td .el-date-table-cell__text { color: var(--text-secondary) !important; }
.el-date-table td.available:hover .el-date-table-cell { background: var(--bg-raised) !important; border-radius: 6px !important; }
.el-date-table td.in-range .el-date-table-cell { background: var(--blue-subtle) !important; }
.el-date-table td.start-date .el-date-table-cell__text,
.el-date-table td.end-date   .el-date-table-cell__text { background: var(--blue) !important; color: #fff !important; border-radius: 50% !important; }
.el-date-table td.disabled .el-date-table-cell__text { color: var(--text-muted) !important; opacity: .5; }
.el-date-range-picker__content.is-left { border-right-color: var(--border) !important; }
.el-year-table td .cell, .el-month-table td .cell { color: var(--text-secondary) !important; }

.el-button {
  background: transparent !important; border: 1px solid var(--border) !important;
  color: var(--text-secondary) !important; border-radius: 6px !important; font-size: 13px !important; transition: all .15s !important;
}
.el-button:hover { border-color: var(--border-hover) !important; color: var(--text-primary) !important; background: var(--bg-overlay) !important; }
.el-button--primary { background: var(--blue-subtle) !important; border-color: var(--blue-muted) !important; color: var(--blue) !important; }
.el-button--primary:hover { background: rgba(56,139,253,.18) !important; border-color: var(--blue) !important; }

.el-tag { border-radius: 4px !important; font-size: 11px !important; padding: 0 7px !important; height: 20px !important; line-height: 18px !important; }
.el-tag--primary { background: var(--blue-subtle) !important; border-color: var(--blue-muted) !important; color: var(--blue) !important; }
.el-tag--success { background: rgba(63,185,80,.1)  !important; border-color: rgba(63,185,80,.3)  !important; color: var(--green) !important; }
.el-tag--warning { background: rgba(210,153,34,.1) !important; border-color: rgba(210,153,34,.3) !important; color: var(--amber) !important; }
.el-tag--danger  { background: rgba(248,81,73,.1)  !important; border-color: rgba(248,81,73,.3)  !important; color: var(--red)   !important; }
.el-tag--info    { background: var(--blue-subtle)   !important; border-color: var(--blue-muted)   !important; color: var(--blue)  !important; }

.el-tabs--border-card { background: var(--bg-raised) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; box-shadow: var(--shadow) !important; }
.el-tabs--border-card > .el-tabs__header { background: var(--bg-base) !important; border-bottom: 1px solid var(--border) !important; border-radius: 8px 8px 0 0 !important; }
.el-tabs--border-card > .el-tabs__header .el-tabs__item { color: var(--text-muted) !important; border: none !important; font-size: 13px !important; font-weight: 500 !important; transition: color .15s !important; }
.el-tabs--border-card > .el-tabs__header .el-tabs__item:hover { color: var(--text-primary) !important; }
.el-tabs--border-card > .el-tabs__header .el-tabs__item.is-active { color: var(--text-primary) !important; background: var(--bg-raised) !important; border-bottom: 2px solid var(--blue) !important; }

.el-pagination { color: var(--text-secondary) !important; }
.el-pager li { background: transparent !important; color: var(--text-secondary) !important; border-radius: 4px !important; }
.el-pager li:hover { color: var(--text-primary) !important; }
.el-pager li.is-active { background: var(--blue-subtle) !important; color: var(--blue) !important; border: 1px solid var(--blue-muted) !important; }
.el-pagination button { background: transparent !important; color: var(--text-secondary) !important; }
.el-pagination button:hover { color: var(--text-primary) !important; }
.el-pagination__total, .el-pagination__jump { color: var(--text-secondary) !important; font-size: 13px !important; }
.el-pagination .el-input__wrapper { background: var(--bg-base) !important; border-color: var(--border) !important; }
.el-empty__description p { color: var(--text-muted) !important; }

/* ═══════════════════════════════════════════════════════
   Element Plus 亮色覆盖（简约风 / light）
   比暗色选择器多一层 [data-theme="light"]，优先级更高
════════════════════════════════════════════════════════ */
[data-theme="light"] .el-card { box-shadow: 0 1px 4px rgba(15,23,42,.07) !important; }
[data-theme="light"] .el-card:hover { border-color: rgba(15,23,42,.16) !important; box-shadow: 0 4px 12px rgba(15,23,42,.1) !important; }

[data-theme="light"] .el-table th.el-table__cell { background: #f8fafc !important; }
[data-theme="light"] .el-table--border { border-color: rgba(15,23,42,.09) !important; }
[data-theme="light"] .el-table__inner-wrapper::before,
[data-theme="light"] .el-table::before { background-color: rgba(15,23,42,.09) !important; }
[data-theme="light"] .el-loading-mask { background: rgba(248,250,252,.8) !important; }


[data-theme="light"] .el-select-dropdown { background: #fff !important; }
[data-theme="light"] .el-select-dropdown__item:hover { background: #f1f5f9 !important; }
[data-theme="light"] .el-popper { background: #fff !important; border-color: rgba(15,23,42,.1) !important; color: var(--text-primary) !important; }
[data-theme="light"] .el-popper.is-light { background: #fff !important; border-color: rgba(15,23,42,.1) !important; }
[data-theme="light"] .el-popper__arrow::before { background: #fff !important; border-color: rgba(15,23,42,.1) !important; }

html[data-theme="light"] .el-picker__popper,
html[data-theme="light"] .el-picker__popper.is-pure,
html[data-theme="light"] .el-picker__popper.el-popper { background: #fff !important; border-color: rgba(15,23,42,.1) !important; }
html[data-theme="light"] .el-picker__popper .el-picker-panel,
html[data-theme="light"] .el-picker-panel,
html[data-theme="light"] .el-picker__popper .el-picker-panel__body-wrapper,
html[data-theme="light"] .el-picker__popper .el-picker-panel__body,
html[data-theme="light"] .el-picker__popper .el-date-range-picker__body,
html[data-theme="light"] .el-picker__popper .el-date-range-picker__content { background: #fff !important; border-color: rgba(15,23,42,.1) !important; }
[data-theme="light"] .el-date-table td.available:hover .el-date-table-cell { background: #f1f5f9 !important; }
[data-theme="light"] .el-date-range-picker__content.is-left { border-right-color: rgba(15,23,42,.08) !important; }

[data-theme="light"] .el-button:hover { background: #f8fafc !important; border-color: rgba(15,23,42,.2) !important; }
[data-theme="light"] .el-button--primary:hover { background: rgba(59,130,246,.15) !important; }

[data-theme="light"] .el-tag--success { background: rgba(22,163,74,.1) !important; border-color: rgba(22,163,74,.3) !important; }
[data-theme="light"] .el-tag--warning { background: rgba(202,138,4,.1)  !important; border-color: rgba(202,138,4,.3)  !important; }
[data-theme="light"] .el-tag--danger  { background: rgba(220,38,38,.1)  !important; border-color: rgba(220,38,38,.3)  !important; }

[data-theme="light"] .el-tabs--border-card { box-shadow: 0 1px 4px rgba(15,23,42,.07) !important; }
[data-theme="light"] .el-tabs--border-card > .el-tabs__header .el-tabs__item.is-active { background: #fff !important; }

[data-theme="light"] .el-pager li.is-active { border-color: rgba(59,130,246,.3) !important; }
</style>
