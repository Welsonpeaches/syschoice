import type { App } from 'vue'
import { ref } from 'vue'

import zhCN from './zh-CN'

export const LOCALES = { 'zh-CN': '简体中文' } as const
export type LocaleKey = keyof typeof LOCALES

const bundles: Record<LocaleKey, Record<string, string>> = {
  'zh-CN': zhCN as unknown as Record<string, string>,
}

export const locale = ref<LocaleKey>('zh-CN')

/** Look up a string, falling back to the key itself so nothing renders blank. */
export function t(key: string, params?: Record<string, string | number>): string {
  const template = bundles[locale.value]?.[key] ?? bundles['zh-CN'][key] ?? key
  if (!params) return template
  return Object.entries(params).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template,
  )
}

export function setLocale(next: LocaleKey) {
  locale.value = next
}

export const i18n = {
  install(app: App) {
    app.config.globalProperties.$t = t
  },
}
