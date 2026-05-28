import axios from 'axios'

const http = axios.create({ baseURL: 'http://localhost:8001' })

export const getOverview        = ()           => http.get('/api/packing/overview')
export const getDailyTrend      = (days = 30)  => http.get('/api/packing/daily-trend', { params: { days } })
export const getWinnerDist      = ()           => http.get('/api/packing/winner-distribution')
export const getAdoptionAnalysis = ()          => http.get('/api/packing/adoption-analysis')
export const getBenefit         = (days = 30)  => http.get('/api/packing/benefit', { params: { days } })
export const getRecords         = (params)     => http.get('/api/packing/records', { params })
export const getFeedbacks       = (params)     => http.get('/api/packing/feedbacks', { params })
export const getFilterOptions   = ()           => http.get('/api/packing/filter-options')
export const getRecordSource    = (resultId)   => http.get(`/api/packing/records/${resultId}/source`)
export const getOptFeedbacks    = (params)     => http.get('/api/packing/optimization-feedbacks', { params })
