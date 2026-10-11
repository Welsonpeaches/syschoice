<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { t } from '@/i18n'

const route = useRoute()
const router = useRouter()

const steps = [
  { name: 'hardware', label: 'step.hardware' },
  { name: 'interview', label: 'step.interview' },
  { name: 'quiz', label: 'step.quiz' },
  { name: 'lab', label: 'step.lab' },
  { name: 'result', label: 'step.result' },
]

const currentIndex = computed(() => steps.findIndex((step) => step.name === route.name))

function markerClass(index: number) {
  if (index === currentIndex.value) return 'border-flux bg-flux text-white shadow-panel'
  if (index < currentIndex.value) return 'border-flux text-flux'
  return 'border-line-strong text-graphite'
}

function labelClass(index: number) {
  if (index === currentIndex.value) return 'font-semibold text-ink'
  if (index < currentIndex.value) return 'text-ink'
  return 'text-mist'
}

function go(step: string, index: number) {
  if (index >= currentIndex.value) return
  router.push({ name: step })
}
</script>

<template>
  <!-- The rail really is a sequence, so the numbered markers carry meaning. -->
  <nav aria-label="测试步骤">
    <ol class="hidden md:block">
      <li v-for="(step, index) in steps" :key="step.name" class="py-1">
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-card px-2.5 py-2.5 text-left transition-colors"
          :disabled="index >= currentIndex"
          :class="
            index === currentIndex
              ? 'bg-flux-soft cursor-default'
              : index < currentIndex
                ? 'cursor-pointer hover:bg-surface-2'
                : 'cursor-default'
          "
          @click="go(step.name, index)"
        >
          <span
            class="mono-value flex h-6 w-6 shrink-0 items-center justify-center border text-[12px]"
            :class="markerClass(index)"
          >
            {{ index + 1 }}
          </span>
          <span class="text-[13px]" :class="labelClass(index)">{{ t(step.label) }}</span>
        </button>
      </li>
    </ol>

    <ol class="flex items-center gap-2 md:hidden">
      <li v-for="(step, index) in steps" :key="step.name" class="flex items-center gap-2">
        <span
          class="mono-value flex h-6 w-6 items-center justify-center border text-[12px]"
          :class="markerClass(index)"
        >
          {{ index + 1 }}
        </span>
        <span
          v-if="index !== steps.length - 1"
          class="h-px w-5"
          :class="index < currentIndex ? 'bg-flux' : 'bg-line-strong'"
        />
      </li>
      <li class="ml-1 text-[13px] font-semibold">
        {{ t(steps[Math.max(currentIndex, 0)].label) }}
      </li>
    </ol>
  </nav>
</template>
