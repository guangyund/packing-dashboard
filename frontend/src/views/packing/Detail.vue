<template>
  <div>
    <el-tabs v-model="activeTab" type="border-card">

      <!-- ── 计算结果明细 ── -->
      <el-tab-pane label="计算结果明细" name="records">

        <!-- 筛选栏 -->
        <div class="filter-bar">
          <div class="filter-item">
            <span class="filter-label">日期范围</span>
            <el-date-picker
              v-model="recFilter.dateRange"
              type="daterange"
              range-separator="~"
              start-placeholder="开始"
              end-placeholder="结束"
              value-format="YYYY-MM-DD"
              style="width:220px"
              size="default"
            />
          </div>

          <div class="filter-item">
            <span class="filter-label">推荐方案</span>
            <el-select v-model="recFilter.winner" placeholder="全部" clearable style="width:120px">
              <el-option v-for="w in filterOpts.winners" :key="w" :label="winnerLabel[w] || w" :value="w" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-label">产品分类</span>
            <el-select v-model="recFilter.product_category" placeholder="全部" clearable style="width:120px">
              <el-option v-for="c in filterOpts.categories" :key="c" :label="c" :value="c" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-label">AI 决策</span>
            <el-select v-model="recFilter.ai_used" placeholder="全部" clearable style="width:96px">
              <el-option label="是" :value="1" />
              <el-option label="否" :value="0" />
            </el-select>
          </div>

          <div class="filter-actions">
            <el-button type="primary" @click="loadRecords(1)">查询</el-button>
            <el-button @click="resetRecFilter">重置</el-button>
            <span v-if="recActiveCount" class="filter-active-badge">{{ recActiveCount }} 个筛选条件</span>
          </div>
        </div>

        <!-- 数据表 -->
        <el-table
          class="records-table"
          :data="recPage.rows"
          border size="small" style="width:100%"
          v-loading="recPage.loading"
          :span-method="spanMethod"
          :row-class-name="recordsRowClass"
          @cell-mouse-enter="onCellEnter"
          @cell-mouse-leave="onCellLeave"
          @mouseleave="onCellLeave"
        >
          <el-table-column prop="created_at"       label="时间"     width="155" fixed />
          <el-table-column prop="product_category" label="产品分类"  width="100" />
          <el-table-column prop="item_count"       label="商品数"   width="70"  align="center" />
          <el-table-column prop="total_weight"     label="总重(kg)" width="85"  align="right" />
          <el-table-column label="推荐方案" width="92" align="center">
            <template #default="{ row }">
              <el-tag :type="winnerTagType[row.winner]" size="small">{{ winnerLabel[row.winner] || row.winner }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="winner_bin"  label="推荐箱型" min-width="160" show-overflow-tooltip />
          <el-table-column prop="winner_tier" label="推荐费档" width="100" />
          <el-table-column label="推荐FBA费" width="95" align="right">
            <template #default="{ row }">{{ row.winner_total_fee ? '$' + row.winner_total_fee : '—' }}</template>
          </el-table-column>
          <el-table-column prop="existing_tier" label="原费档" width="100" />
          <el-table-column label="原FBA费" width="90" align="right">
            <template #default="{ row }">{{ row.existing_total_fee ? '$' + row.existing_total_fee : '—' }}</template>
          </el-table-column>
          <el-table-column label="节省费用" width="90" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.fee_saved > 0 ? 'var(--green)' : 'var(--text-muted)' }">
                {{ row.fee_saved > 0 ? '$' + row.fee_saved : '—' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="降档" width="62" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.tier_upgraded" type="success" size="small">是</el-tag>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="利用率" width="72" align="center">
            <template #default="{ row }">{{ row.utilization_pct != null ? row.utilization_pct + '%' : '—' }}</template>
          </el-table-column>
          <el-table-column label="现有前3优利用率" width="130" align="center">
            <template #default="{ row }">
              <template v-if="parseTop3(row.top3_existing_json).length">
                <el-tooltip placement="top" :show-after="200">
                  <template #content>
                    <div v-for="(t, i) in parseTop3(row.top3_existing_json)" :key="i" style="white-space:nowrap;line-height:1.8">
                      <span style="color:#aaa">{{ '#' + (i+1) }}</span>
                      {{ t.bin_type }}
                      <span :style="{ color: t.utilization < 0.3 ? '#f56c6c' : t.utilization < 0.6 ? '#e6a23c' : '#67c23a' }">
                        {{ (t.utilization * 100).toFixed(0) + '%' }}
                      </span>
                    </div>
                  </template>
                  <span class="top3-util-text">
                    {{ parseTop3(row.top3_existing_json).map(t => (t.utilization*100).toFixed(0)+'%').join(' / ') }}
                  </span>
                </el-tooltip>
              </template>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="AI" width="60" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.ai_used" type="primary" size="small">AI</el-tag>
              <span v-else class="dim">本地</span>
            </template>
          </el-table-column>
          <el-table-column label="AI 模型" width="110" align="center">
            <template #default="{ row }">
              <template v-if="row.ai_model">
                <div v-if="row.ai_provider" class="provider-label">{{ row.ai_provider }}</div>
                <span class="model-tag">{{ modelLabel[row.ai_model] || row.ai_model }}</span>
              </template>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="装箱输入 Token" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.ai_input_tokens != null">{{ row.ai_input_tokens.toLocaleString() }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="装箱输出 Token" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.ai_output_tokens != null">{{ row.ai_output_tokens.toLocaleString() }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="防护分析来源" width="104" align="center">
            <template #default="{ row }">
              <template v-if="row.classify_source === 'ai'">
                <el-tag type="primary" size="small">AI</el-tag>
                <div class="classify-model-label">
                  <span v-if="row.classify_provider" class="provider-label">{{ row.classify_provider }}</span>
                  {{ row.classify_model ? (classifyModelLabel[row.classify_model] || row.classify_model) : '' }}
                </div>
              </template>
              <el-tag v-else-if="row.classify_source === 'keyword'" type="info" size="small">本地规则</el-tag>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="分析输入 Token" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.classify_input_tokens != null" style="color:var(--amber)">
                {{ row.classify_input_tokens.toLocaleString() }}
              </span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="分析输出 Token" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.classify_output_tokens != null" style="color:var(--amber)">
                {{ row.classify_output_tokens.toLocaleString() }}
              </span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="包材类型" width="76" align="center">
            <template #default="{ row }">
              <span v-if="row.plan_type" class="plan-type-tag">{{ row.plan_type }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="计算耗时" width="90" align="right">
            <template #default="{ row }">
              <template v-if="row.duration_ms != null">
                <span :style="{ color: row.duration_ms > 30000 ? 'var(--amber)' : 'var(--text-secondary)' }">
                  {{ row.duration_ms >= 1000 ? (row.duration_ms / 1000).toFixed(1) + 's' : row.duration_ms + 'ms' }}
                </span>
              </template>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="计算编号" width="148" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.calc_no" class="no-cell">{{ row.calc_no }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="方案编号" width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.plan_no" class="no-cell">{{ row.plan_no }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="方案ID" width="80" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="id-cell" :title="row.result_id">{{ row.result_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="计算ID" width="80" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.session_id" class="id-cell" :title="row.session_id">{{ row.session_id }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" align="center" fixed="right">
            <template #default="{ row }">
              <button class="src-btn" @click="openSource(row.result_id)">数据来源</button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="recPage.page"
            :page-size="recPage.page_size"
            :total="recPage.total"
            layout="total, prev, pager, next"
            @current-change="loadRecords"
          />
        </div>
      </el-tab-pane>

      <!-- ── 反馈情况明细 ── -->
      <el-tab-pane label="反馈情况明细" name="feedbacks">

        <!-- 筛选栏 -->
        <div class="filter-bar">
          <div class="filter-item">
            <span class="filter-label">日期范围</span>
            <el-date-picker
              v-model="fbFilter.dateRange"
              type="daterange"
              range-separator="~"
              start-placeholder="开始"
              end-placeholder="结束"
              value-format="YYYY-MM-DD"
              style="width:220px"
            />
          </div>

          <div class="filter-item">
            <span class="filter-label">选择方案</span>
            <el-select v-model="fbFilter.selected_plan" placeholder="全部" clearable style="width:120px">
              <el-option label="推荐新包材" value="rec" />
              <el-option label="软包材"     value="soft" />
              <el-option label="包材库最优"  value="best" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-label">采纳状态</span>
            <el-select v-model="fbFilter.adopted" placeholder="全部" clearable style="width:100px">
              <el-option label="已采纳" :value="1" />
              <el-option label="未采纳" :value="0" />
            </el-select>
          </div>

          <div class="filter-actions">
            <el-button type="primary" @click="loadFeedbacks(1)">查询</el-button>
            <el-button @click="resetFbFilter">重置</el-button>
            <span v-if="fbActiveCount" class="filter-active-badge">{{ fbActiveCount }} 个筛选条件</span>
          </div>
        </div>

        <!-- 数据表 -->
        <el-table :data="fbPage.rows" border size="small" style="width:100%" v-loading="fbPage.loading">
          <el-table-column prop="created_at" label="反馈时间" width="155" fixed />
          <el-table-column label="包材类型" width="76" align="center">
            <template #default="{ row }">
              <span v-if="row.plan_type" class="plan-type-tag">{{ row.plan_type }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="采纳状态" width="82" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.adopted === 1"  type="success" size="small">已采纳</el-tag>
              <el-tag v-else-if="row.adopted === 0" type="danger" size="small">未采纳</el-tag>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="选择方案" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="winnerTagType[row.selected_plan]" size="small">
                {{ row.selected_plan === 'best' && row.selected_rank > 1
                   ? `包材库第${row.selected_rank}优`
                   : winnerLabel[row.selected_plan] || row.selected_plan || '—' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="选择方式" width="88" align="center">
            <template #default="{ row }">{{ methodLabel[row.selection_method] || row.selection_method || '—' }}</template>
          </el-table-column>
          <el-table-column prop="recommended_bin"  label="推荐箱型"   width="160" show-overflow-tooltip />
          <el-table-column prop="actual_used_bin"  label="实际使用箱型" width="160" show-overflow-tooltip />
          <el-table-column prop="reason_changed"   label="未采纳原因" width="130" show-overflow-tooltip />
          <el-table-column prop="reason_detail"    label="详细说明"   min-width="150" show-overflow-tooltip />
          <el-table-column prop="operator_id"      label="操作人"     width="96"  show-overflow-tooltip />
          <el-table-column prop="updated_at"       label="更新时间"   width="155" />
          <el-table-column label="计算编号" width="148" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.calc_no" class="no-cell">{{ row.calc_no }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="方案编号" width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.plan_no" class="no-cell">{{ row.plan_no }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column label="方案ID" width="80" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="id-cell" :title="row.result_id">{{ row.result_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="计算ID" width="80" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.session_id" class="id-cell" :title="row.session_id">{{ row.session_id }}</span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="fbPage.page"
            :page-size="fbPage.page_size"
            :total="fbPage.total"
            layout="total, prev, pager, next"
            @current-change="loadFeedbacks"
          />
        </div>
      </el-tab-pane>

      <!-- ── 优化反馈 ── -->
      <el-tab-pane label="优化反馈" name="optfeedbacks">

        <div class="filter-bar">
          <div class="filter-item">
            <span class="filter-label">反馈类别</span>
            <el-select v-model="optFbFilter.category" placeholder="全部" clearable style="width:140px">
              <el-option label="推荐不准确"   value="推荐不准确" />
              <el-option label="AI分类有误"   value="AI分类有误" />
              <el-option label="尺寸/重量问题" value="尺寸/重量问题" />
              <el-option label="包材库问题"   value="包材库问题" />
              <el-option label="操作体验"     value="操作体验" />
              <el-option label="其他"         value="其他" />
            </el-select>
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="loadOptFeedbacks(1)">查询</el-button>
            <el-button @click="resetOptFbFilter">重置</el-button>
          </div>
        </div>

        <el-table :data="optFbPage.rows" border size="small" style="width:100%" v-loading="optFbPage.loading">
          <el-table-column prop="created_at" label="提交时间" width="155" fixed />
          <el-table-column prop="category"   label="类别"     width="120" />
          <el-table-column prop="content"    label="反馈内容" min-width="240" show-overflow-tooltip />
          <el-table-column prop="result_id"  label="关联计算ID" width="100" show-overflow-tooltip />
          <el-table-column prop="operator_id" label="操作人"   width="96" show-overflow-tooltip />
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="optFbPage.page"
            :page-size="optFbPage.page_size"
            :total="optFbPage.total"
            layout="total, prev, pager, next"
            @current-change="loadOptFeedbacks"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 数据来源弹窗 -->
    <el-dialog v-model="sourceDialog.visible" title="数据来源" width="860px" destroy-on-close>
      <div v-loading="sourceDialog.loading">

        <!-- 货品明细 -->
        <div class="source-section-title">货品明细（{{ sourceDialog.items.length }} 件）</div>
        <el-table :data="sourceDialog.items" border size="small" style="width:100%;margin-bottom:20px">
          <el-table-column prop="item_id"          label="商品ID"   width="110" show-overflow-tooltip />
          <el-table-column label="尺寸 L×W×H (cm)" width="140" align="center">
            <template #default="{ row }">{{ row.length }}×{{ row.width }}×{{ row.height }}</template>
          </el-table-column>
          <el-table-column prop="weight"           label="重量(kg)" width="80"  align="right" />
          <el-table-column prop="product_title"    label="品名"     min-width="130" show-overflow-tooltip />
          <el-table-column prop="sale_price"       label="售价($)"  width="80"  align="right" />
          <el-table-column prop="product_category" label="分类"     width="100" show-overflow-tooltip />
          <el-table-column label="软包材许可" width="82" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.soft_packaging_ok" type="success" size="small">是</el-tag>
              <span v-else class="dim">否</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 自填包材 -->
        <template v-if="sourceDialog.inputBins.length">
          <div class="source-section-title">用户自填包材（{{ sourceDialog.inputBins.length }} 条）</div>
          <el-table :data="sourceDialog.inputBins" border size="small" style="width:100%">
            <el-table-column prop="type"       label="箱型"         min-width="160" show-overflow-tooltip />
            <el-table-column label="尺寸 L×W×H (cm)" width="140" align="center">
              <template #default="{ row }">{{ row.length }}×{{ row.width }}×{{ row.height }}</template>
            </el-table-column>
            <el-table-column prop="max_weight" label="最大承重(kg)" width="110" align="right" />
          </el-table>
        </template>
        <div v-else class="source-no-bins">本次计算未填写自定义包材</div>

      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getRecords, getFeedbacks, getFilterOptions, getRecordSource, getOptFeedbacks } from '../../api/packing.js'

const activeTab = ref('records')

const winnerLabel   = { rec: '推荐新包材', soft: '软包材', best: '包材库最优' }
const winnerTagType = { rec: 'primary', soft: 'warning', best: 'success' }
const methodLabel   = { default: '系统默认', auto: '静默自动', manual: '手动选择' }
const modelLabel    = {
  'claude-haiku-4-5-20251001': 'Haiku 4.5',
  'claude-haiku-4-5':          'Haiku 4.5',
  'claude-sonnet-4-6':         'Sonnet 4.6',
  'claude-opus-4-7':           'Opus 4.7',
}
const parseTop3 = (json) => {
  if (!json) return []
  try {
    const arr = typeof json === 'string' ? JSON.parse(json) : json
    return Array.isArray(arr) ? arr.map(e => ({
      bin_type:    e.bin_type || '',
      utilization: (e.result?.utilization ?? e.bin_result?.utilization ?? 0),
    })) : []
  } catch { return [] }
}

const classifyModelLabel = {
  'claude-haiku-4-5-20251001': 'Haiku 4.5',
  'claude-haiku-4-5':          'Haiku 4.5',
  'claude-sonnet-4-6':         'Sonnet 4.6',
}

/* ── 计算结果 ─────────────────────────────────────────────── */
const recFilter  = ref({ dateRange: null, winner: null, product_category: null, ai_used: null })
const recPage    = ref({ rows: [], total: 0, page: 1, page_size: 20, loading: false })

// 防护分析来源、分析输入Token、分析输出Token 按 calc_no 合并行
// 用 column.label 匹配，避免 fixed 列导致 columnIndex 偏移
const CLASSIFY_MERGE_LABELS = new Set(['防护分析来源', '分析输入 Token', '分析输出 Token'])

const calcNoSpanMap = computed(() => {
  const rows = recPage.value.rows
  const map = {}
  let i = 0
  while (i < rows.length) {
    const cn = rows[i].calc_no
    if (!cn) { map[i] = 1; i++; continue }
    let j = i
    while (j < rows.length && rows[j].calc_no === cn) j++
    const cnt = j - i
    for (let k = i; k < j; k++) map[k] = k === i ? cnt : 0
    i = j
  }
  return map
})

const spanMethod = ({ rowIndex, column }) => {
  if (CLASSIFY_MERGE_LABELS.has(column.label)) {
    const span = calcNoSpanMap.value[rowIndex]
    if (span === 0) return [0, 0]
    if (span != null) return [span, 1]
  }
  return [1, 1]
}

// JS 驱动的 hover：同组所有行同时高亮，解决跨行 rowspan 时 hover 颜色不一致的问题
const hoveredCalcNo = ref(null)
const onCellEnter = (row) => { hoveredCalcNo.value = row.calc_no || null }
const onCellLeave = () => { hoveredCalcNo.value = null }
const recordsRowClass = ({ row }) =>
  row.calc_no && row.calc_no === hoveredCalcNo.value ? 'group-hovered' : ''
const filterOpts = ref({ winners: [], categories: [] })

const recActiveCount = computed(() => {
  const f = recFilter.value
  return [f.dateRange, f.winner, f.product_category, f.ai_used != null ? f.ai_used : null].filter(v => v != null).length
})

function buildRecParams(page) {
  const p = { page, page_size: recPage.value.page_size }
  if (recFilter.value.dateRange)        { p.date_from = recFilter.value.dateRange[0]; p.date_to = recFilter.value.dateRange[1] }
  if (recFilter.value.winner)           p.winner           = recFilter.value.winner
  if (recFilter.value.product_category) p.product_category = recFilter.value.product_category
  if (recFilter.value.ai_used != null)  p.ai_used          = recFilter.value.ai_used
  return p
}

// 同 calc_no 组内，把有 classify 数据的行移到首位（API 按 created_at DESC 排，方案A最晚写入）
function prioritizeClassifyRow(rows) {
  const result = []
  let i = 0
  while (i < rows.length) {
    const cn = rows[i].calc_no
    if (!cn) { result.push(rows[i]); i++; continue }
    let j = i
    while (j < rows.length && rows[j].calc_no === cn) j++
    const group = rows.slice(i, j)
    const idx = group.findIndex(r => r.classify_source != null)
    if (idx > 0) { const [r] = group.splice(idx, 1); group.unshift(r) }
    result.push(...group)
    i = j
  }
  return result
}

async function loadRecords(page = 1) {
  recPage.value.loading = true
  try {
    const res = await getRecords(buildRecParams(page))
    const rows = prioritizeClassifyRow(res.data.rows || [])
    Object.assign(recPage.value, { rows, total: res.data.total, page: res.data.page })
  } finally { recPage.value.loading = false }
}

function resetRecFilter() {
  recFilter.value = { dateRange: null, winner: null, product_category: null, ai_used: null }
  loadRecords(1)
}

/* ── 反馈明细 ─────────────────────────────────────────────── */
const fbFilter = ref({ dateRange: null, selected_plan: null, adopted: null })
const fbPage   = ref({ rows: [], total: 0, page: 1, page_size: 20, loading: false })

const fbActiveCount = computed(() => {
  const f = fbFilter.value
  return [f.dateRange, f.selected_plan, f.adopted != null ? f.adopted : null].filter(v => v != null).length
})

function buildFbParams(page) {
  const p = { page, page_size: fbPage.value.page_size }
  if (fbFilter.value.dateRange)         { p.date_from = fbFilter.value.dateRange[0]; p.date_to = fbFilter.value.dateRange[1] }
  if (fbFilter.value.selected_plan)     p.selected_plan = fbFilter.value.selected_plan
  if (fbFilter.value.adopted != null)   p.adopted       = fbFilter.value.adopted
  return p
}

async function loadFeedbacks(page = 1) {
  fbPage.value.loading = true
  try {
    const res = await getFeedbacks(buildFbParams(page))
    Object.assign(fbPage.value, { rows: res.data.rows, total: res.data.total, page: res.data.page })
  } finally { fbPage.value.loading = false }
}

function resetFbFilter() {
  fbFilter.value = { dateRange: null, selected_plan: null, adopted: null }
  loadFeedbacks(1)
}

/* ── 数据来源弹窗 ─────────────────────────────────────────────── */
const sourceDialog = ref({ visible: false, loading: false, items: [], inputBins: [] })

async function openSource(resultId) {
  sourceDialog.value = { visible: true, loading: true, items: [], inputBins: [] }
  try {
    const res = await getRecordSource(resultId)
    sourceDialog.value.items     = res.data.items     || []
    sourceDialog.value.inputBins = res.data.input_bins || []
  } finally {
    sourceDialog.value.loading = false
  }
}

/* ── 优化反馈 ─────────────────────────────────────────────── */
const optFbFilter = ref({ category: null })
const optFbPage   = ref({ rows: [], total: 0, page: 1, page_size: 20, loading: false })

async function loadOptFeedbacks(page = 1) {
  optFbPage.value.loading = true
  try {
    const params = { page, page_size: optFbPage.value.page_size }
    if (optFbFilter.value.category) params.category = optFbFilter.value.category
    const res = await getOptFeedbacks(params)
    Object.assign(optFbPage.value, { rows: res.data.items, total: res.data.total, page })
  } finally { optFbPage.value.loading = false }
}

function resetOptFbFilter() {
  optFbFilter.value = { category: null }
  loadOptFeedbacks(1)
}

watch(activeTab, tab => {
  if (tab === 'records')      loadRecords(1)
  if (tab === 'feedbacks')    loadFeedbacks(1)
  if (tab === 'optfeedbacks') loadOptFeedbacks(1)
})

onMounted(async () => {
  const res = await getFilterOptions()
  filterOpts.value = res.data
  loadRecords(1)
})
</script>

<style scoped>
/* ── 筛选栏 ──────────────────────────────────────────────── */
.filter-bar {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: 7px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: .4px;
  text-transform: uppercase;
  user-select: none;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  padding-bottom: 1px; /* 与输入框底部对齐 */
}

.filter-active-badge {
  font-size: 11px;
  color: var(--blue);
  background: var(--blue-subtle);
  border: 1px solid var(--blue-muted);
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

/* ── 分页 ────────────────────────────────────────────────── */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

/* ── 表格内 dim 文字 ─────────────────────────────────────── */
.dim { color: var(--text-muted); }

/* ── records-table hover 修复（跨行 rowspan 场景）──────────── */
/* group-hovered 用 !important 盖过 El Plus 默认 hover-row，同组所有行同步高亮 */
/* 直接用 --bg-overlay，不用 --el-table-row-hover-bg-color（El Plus 在组件元素本身重定义了该变量，
   html[data-theme] 级覆盖对其无效，会导致 hover 变白） */
.records-table :deep(tr.group-hovered > td.el-table__cell) {
  background-color: var(--bg-overlay) !important;
}

.provider-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-bottom: 2px;
  line-height: 1.2;
}

.model-tag {
  font-size: 11px;
  font-weight: 600;
  color: #a371f7;
  background: rgba(163,113,247,.1);
  border: 1px solid rgba(163,113,247,.25);
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

/* ── 数据来源弹窗 ──────────────────────────────────────── */
.source-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.source-no-bins {
  font-size: 12px;
  color: var(--text-muted);
  padding: 8px 0;
}

/* ── ID 单元格 ─────────────────────────────────────────────── */
.id-cell {
  font-size: 11px;
  font-family: monospace;
  color: var(--text-muted);
  cursor: default;
}

/* ── 编号单元格（计算编号 / 方案编号）──────────────────────── */
.no-cell {
  font-size: 12px;
  font-family: monospace;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

/* ── 包材类型标签 ─────────────────────────────────────────── */
.classify-model-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  line-height: 1.2;
}

.top3-util-text {
  font-size: 12px;
  color: var(--text-secondary);
  cursor: default;
  border-bottom: 1px dashed var(--border);
}

.plan-type-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

/* ── 数据来源按钮 ─────────────────────────────────────────── */
.src-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 500;
  color: var(--blue);
  background: var(--blue-subtle);
  border: 1px solid var(--blue-muted);
  border-radius: 5px;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s, border-color .15s;
  line-height: 18px;
}
.src-btn:hover {
  background: color-mix(in srgb, var(--blue) 18%, transparent);
  border-color: var(--blue);
}
</style>
