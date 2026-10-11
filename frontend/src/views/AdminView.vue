<script setup lang="ts">
import { Download, Loader2, LogOut, Search } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'

import { ApiError, api } from '@/api/client'
import type { AdminSessionsResponse } from '@/api/types'
import { t } from '@/i18n'

const TOKEN_KEY = 'syschoice.adminToken'

const token = ref('')
const authorised = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
const page = ref(1)
const query = ref('')
const data = ref<AdminSessionsResponse | null>(null)

const totalPages = computed(() =>
  data.value ? Math.max(1, Math.ceil(data.value.total / data.value.pageSize)) : 1,
)

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await api.adminSessions(token.value, page.value, query.value)
    authorised.value = true
    localStorage.setItem(TOKEN_KEY, token.value)
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      authorised.value = false
      error.value = t('admin.badToken')
    } else {
      error.value = err instanceof Error ? err.message : '加载失败'
    }
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function go(delta: number) {
  const next = page.value + delta
  if (next < 1 || next > totalPages.value) return
  page.value = next
  load()
}

function signOut() {
  localStorage.removeItem(TOKEN_KEY)
  token.value = ''
  authorised.value = false
  data.value = null
}

async function exportCsv() {
  // The export endpoint needs the token header, so fetch it and download a blob.
  const response = await fetch(api.exportUrl, { headers: { 'X-Admin-Token': token.value } })
  if (!response.ok) {
    error.value = '导出失败，请检查令牌。'
    return
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'syschoice-sessions.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function shortDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  const saved = localStorage.getItem(TOKEN_KEY)
  if (saved) {
    token.value = saved
    load()
  }
})
</script>

<template>
  <section>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-[22px] font-semibold">{{ t('admin.title') }}</h1>
      <button
        v-if="authorised"
        type="button"
        class="btn-quiet px-3 py-1.5 text-[12px]"
        @click="signOut"
      >
        <LogOut :size="14" />
        退出
      </button>
    </div>

    <form v-if="!authorised" class="mt-6 max-w-sm" @submit.prevent="load">
      <label class="block">
        <span class="text-[12px] text-graphite">{{ t('admin.token') }}</span>
        <input v-model="token" type="password" class="field-input mt-1.5" autocomplete="off" />
      </label>
      <button type="submit" class="btn-primary mt-3" :disabled="!token || loading">
        <Loader2 v-if="loading" :size="15" class="animate-spin" />
        {{ t('admin.enter') }}
      </button>
      <p v-if="error" class="mt-3 text-[13px] text-alert">{{ error }}</p>
    </form>

    <template v-else-if="data">
      <div class="mt-6 flex flex-wrap items-center gap-3">
        <label class="flex min-w-[240px] flex-1 items-center gap-2 border border-line-strong bg-white px-3 py-2">
          <Search :size="15" class="text-graphite" />
          <input
            v-model="query"
            class="w-full bg-transparent text-[13px] outline-none"
            :placeholder="t('admin.search')"
            @keyup.enter="search"
          />
        </label>
        <button type="button" class="btn-quiet" @click="search">搜索</button>
        <button type="button" class="btn-quiet" @click="exportCsv">
          <Download :size="15" />
          {{ t('admin.export') }}
        </button>
      </div>

      <p class="mono-value mt-4 text-[12px] text-graphite">
        {{ data.total }} 条记录 · {{ t('admin.page', { page: data.page }) }} / {{ totalPages }}
      </p>

      <div class="mt-3 overflow-x-auto border border-line">
        <table class="w-full min-w-[720px] border-collapse text-[13px]">
          <thead>
            <tr class="border-b border-line bg-paper-2 text-left text-[12px] text-graphite">
              <th class="px-3 py-2 font-medium">分享码</th>
              <th class="px-3 py-2 font-medium">时间</th>
              <th class="px-3 py-2 font-medium">首选系统</th>
              <th class="px-3 py-2 font-medium">系统族</th>
              <th class="px-3 py-2 font-medium text-right">匹配度</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in data.items" :key="row.id" class="border-b border-line last:border-b-0">
              <td class="mono-value px-3 py-2">{{ row.share_code }}</td>
              <td class="mono-value px-3 py-2 text-graphite">{{ shortDate(row.created_at) }}</td>
              <td class="px-3 py-2">{{ row.top1_name ?? '-' }}</td>
              <td class="px-3 py-2 text-graphite">{{ row.top1_family ?? '-' }}</td>
              <td class="mono-value px-3 py-2 text-right">{{ row.top1_match ?? '-' }}</td>
            </tr>
            <tr v-if="!data.items.length">
              <td colspan="5" class="px-3 py-6 text-center text-graphite">{{ t('common.empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-4 flex items-center gap-3">
        <button type="button" class="btn-quiet px-3 py-1.5 text-[12px]" :disabled="page <= 1" @click="go(-1)">
          {{ t('admin.prev') }}
        </button>
        <button
          type="button"
          class="btn-quiet px-3 py-1.5 text-[12px]"
          :disabled="page >= totalPages"
          @click="go(1)"
        >
          {{ t('admin.next') }}
        </button>
      </div>
    </template>
  </section>
</template>
