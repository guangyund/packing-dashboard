import { ref, watch } from 'vue'

const STORAGE_KEY = 'ui-theme'
export const theme = ref(localStorage.getItem(STORAGE_KEY) || 'dark')

// 立即将 data-theme 写入 html 元素，CSS 选择器据此切换
watch(theme, val => {
  localStorage.setItem(STORAGE_KEY, val)
  document.documentElement.setAttribute('data-theme', val)
}, { immediate: true })

export const isDark = () => theme.value === 'dark'
