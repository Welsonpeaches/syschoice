<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import StepRail from '@/components/StepRail.vue'
import { t } from '@/i18n'

const route = useRoute()

const showRail = computed(() => ['hardware', 'quiz', 'lab'].includes(String(route.name)))
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="border-b border-line">
      <div class="mx-auto flex max-w-[1180px] items-center justify-between px-5 py-3.5">
        <RouterLink to="/" class="flex items-baseline gap-2.5">
          <span class="text-[15px] font-semibold">{{ t('app.name') }}</span>
          <span class="mono-value hidden text-[11px] text-graphite sm:inline">sys-choice</span>
        </RouterLink>
        <nav class="flex items-center gap-5 text-[13px]">
          <RouterLink to="/stats" class="text-graphite hover:text-ink">{{ t('nav.stats') }}</RouterLink>
          <RouterLink to="/admin" class="text-graphite hover:text-ink">{{ t('nav.admin') }}</RouterLink>
          <RouterLink to="/test/hardware" class="btn-quiet px-3 py-1.5 text-[13px]">
            {{ t('nav.start') }}
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="flex-1">
      <div
        v-if="showRail"
        class="mx-auto grid max-w-[1180px] gap-8 px-5 py-8 md:grid-cols-[190px_minmax(0,1fr)]"
      >
        <StepRail />
        <div class="min-w-0"><RouterView /></div>
      </div>
      <div v-else class="mx-auto max-w-[1180px] px-5 py-8">
        <RouterView />
      </div>
    </main>

    <footer class="border-t border-line">
      <div class="mx-auto max-w-[1180px] px-5 py-5 text-[12px] text-graphite">
        推荐结果全部由本地评分模型生成，不联网采集你的浏览数据。
      </div>
    </footer>
  </div>
</template>
