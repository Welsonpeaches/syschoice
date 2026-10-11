<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import StepRail from '@/components/StepRail.vue'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const route = useRoute()
const store = useAssessmentStore()

const showRail = computed(() =>
  ['hardware', 'interview', 'quiz', 'lab'].includes(String(route.name)),
)

// The questionnaire and catalog are static, so fetch them once up front and
// every step transition is instant.
onMounted(() => {
  store.ensureLoaded()
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
      <div class="mx-auto flex max-w-[1180px] items-center justify-between px-5 py-3.5">
        <RouterLink to="/" class="group flex items-center gap-2.5">
          <span
            class="flex h-7 w-7 items-center justify-center rounded-card bg-flux text-[13px] font-semibold text-white shadow-panel"
          >
            S
          </span>
          <span class="text-[15px] font-semibold transition-colors group-hover:text-flux-deep">
            {{ t('app.name') }}
          </span>
        </RouterLink>
        <nav class="flex items-center gap-5 text-[13px]">
          <RouterLink
            to="/stats"
            class="text-graphite transition-colors hover:text-flux-deep"
          >
            {{ t('nav.stats') }}
          </RouterLink>
          <RouterLink
            to="/admin"
            class="text-graphite transition-colors hover:text-flux-deep"
          >
            {{ t('nav.admin') }}
          </RouterLink>
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
        <div class="min-w-0">
          <RouterView v-slot="{ Component }">
            <Transition name="step" mode="out-in">
              <component :is="Component" />
            </Transition>
          </RouterView>
        </div>
      </div>
      <div v-else class="mx-auto max-w-[1180px] px-5 py-8">
        <RouterView v-slot="{ Component }">
          <Transition name="step" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </div>
    </main>

    <footer class="mt-8 border-t border-line bg-surface/60">
      <div class="mx-auto max-w-[1180px] px-5 py-5 text-[12px] text-graphite">
        推荐结果全部由本地评分模型生成，不联网采集你的浏览数据。
      </div>
    </footer>
  </div>
</template>
