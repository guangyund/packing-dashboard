import axios from 'axios'

const http = axios.create({ baseURL: 'http://localhost:8001' })

export const getAnomalyStats = (days = 7)  => http.get('/api/anomaly/stats', { params: { days } })
export const getAnomalyList  = (params)    => http.get('/api/anomaly/list',  { params })
