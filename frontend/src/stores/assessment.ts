import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api } from '@/api/client'
import type {
  AssessResult,
  CatalogResponse,
  HardwareReading,
  QuizResponse,
} from '@/api/types'

const HISTORY_KEY = 'syschoice.history'

export interface HistoryEntry {
  shareCode: string
  createdAt: string
  topName: string
  match: number
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : []
  } catch {
    return []
  }
}

export const useAssessmentStore = defineStore('assessment', () => {
  const quiz = ref<QuizResponse | null>(null)
  const catalog = ref<CatalogResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const answers = ref<Record<string, string | string[] | number>>({})
  const cli = ref<Record<string, string>>({})
  const software = ref<string[]>([])
  const scenarios = ref<Record<string, string>>({})
  const hardware = ref<HardwareReading>({})
  // Steps are order-guarded, so the hardware step records that it was seen.
  const hardwareVisited = ref(false)

  const result = ref<AssessResult | null>(null)
  const history = ref<HistoryEntry[]>(loadHistory())
  const startedAt = ref<number | null>(null)

  const questions = computed(() => quiz.value?.questions ?? [])
  const sections = computed(() => quiz.value?.sections ?? [])

  const answeredCount = computed(
    () =>
      questions.value.filter((question) => {
        const value = answers.value[question.id]
        return Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null
      }).length,
  )

  const quizComplete = computed(
    () => questions.value.length > 0 && answeredCount.value === questions.value.length,
  )

  const cliComplete = computed(
    () => (catalog.value?.cli.length ?? 0) > 0 && Object.keys(cli.value).length === catalog.value?.cli.length,
  )

  const scenarioComplete = computed(
    () => (catalog.value?.scenarios.length ?? 0) > 0 && Object.keys(scenarios.value).length === catalog.value?.scenarios.length,
  )

  async function ensureLoaded() {
    if (quiz.value && catalog.value) return
    loading.value = true
    error.value = null
    try {
      const [quizData, catalogData] = await Promise.all([api.quiz(), api.catalog()])
      quiz.value = quizData
      catalog.value = catalogData
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  function begin() {
    startedAt.value = Date.now()
  }

  function setAnswer(questionId: string, value: string | string[] | number) {
    answers.value = { ...answers.value, [questionId]: value }
  }

  function toggleMulti(questionId: string, optionId: string, max?: number) {
    const current = Array.isArray(answers.value[questionId])
      ? [...(answers.value[questionId] as string[])]
      : []
    const index = current.indexOf(optionId)
    if (index >= 0) current.splice(index, 1)
    else if (!max || current.length < max) current.push(optionId)
    setAnswer(questionId, current)
  }

  function setCli(questionId: string, optionId: string) {
    cli.value = { ...cli.value, [questionId]: optionId }
  }

  function setScenario(questionId: string, optionId: string) {
    scenarios.value = { ...scenarios.value, [questionId]: optionId }
  }

  function toggleSoftware(id: string) {
    const next = [...software.value]
    const index = next.indexOf(id)
    if (index >= 0) next.splice(index, 1)
    else next.push(id)
    software.value = next
  }

  function setHardware(reading: HardwareReading) {
    hardware.value = reading
    hardwareVisited.value = true
  }

  function rememberResult(data: AssessResult) {
    const entry: HistoryEntry = {
      shareCode: data.shareCode,
      createdAt: data.createdAt,
      topName: data.top[0]?.name ?? '',
      match: data.top[0]?.match ?? 0,
    }
    history.value = [entry, ...history.value.filter((item) => item.shareCode !== entry.shareCode)].slice(0, 12)
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value))
    } catch {
      /* storage may be unavailable; history is a convenience only */
    }
  }

  async function submit() {
    loading.value = true
    error.value = null
    try {
      const data = await api.assess({
        answers: answers.value,
        scenarios: scenarios.value,
        cli: cli.value,
        software: software.value,
        hardware: hardware.value,
        durationMs: startedAt.value ? Date.now() - startedAt.value : undefined,
      })
      result.value = data
      rememberResult(data)
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '提交失败'
      return null
    } finally {
      loading.value = false
    }
  }

  async function loadResult(code: string) {
    loading.value = true
    error.value = null
    try {
      result.value = await api.result(code)
      return result.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : '读取失败'
      return null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    answers.value = {}
    cli.value = {}
    software.value = []
    scenarios.value = {}
    result.value = null
    startedAt.value = null
  }

  return {
    quiz,
    catalog,
    loading,
    error,
    answers,
    cli,
    software,
    scenarios,
    hardware,
    hardwareVisited,
    result,
    history,
    questions,
    sections,
    answeredCount,
    quizComplete,
    cliComplete,
    scenarioComplete,
    ensureLoaded,
    begin,
    setAnswer,
    toggleMulti,
    setCli,
    setScenario,
    toggleSoftware,
    setHardware,
    submit,
    loadResult,
    reset,
  }
})
