import { createRouter, createWebHashHistory } from 'vue-router'
import PackingOverview from '../views/packing/Overview.vue'
import PackingAdoption from '../views/packing/Adoption.vue'
import PackingBenefit  from '../views/packing/Benefit.vue'
import PackingDetail   from '../views/packing/Detail.vue'
import PackingAnomaly  from '../views/packing/Anomaly.vue'

const routes = [
  { path: '/', redirect: '/packing/overview' },
  { path: '/packing/overview', component: PackingOverview, meta: { title: '使用概览' } },
  { path: '/packing/adoption', component: PackingAdoption, meta: { title: '采纳率分析' } },
  { path: '/packing/benefit',  component: PackingBenefit,  meta: { title: '效益量化' } },
  { path: '/packing/detail',   component: PackingDetail,   meta: { title: '明细查询' } },
  { path: '/packing/anomaly',  component: PackingAnomaly,  meta: { title: '异常监控' } },
]

export default createRouter({ history: createWebHashHistory(), routes })
