import axios from 'axios'

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '' })

export const getAnomalyStats = (days = 7)  => http.get('/api/anomaly/stats', { params: { days } })
export const getAnomalyList  = (params)    => http.get('/api/anomaly/list',  { params })
