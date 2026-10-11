import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAssessmentStore } from '@/stores/assessment'

const quiz = {
  version: '1.0',
  sections: [{ id: 'scene', title: '使用场景', desc: '' }],
  questions: [
    { id: 'A1', section: 'scene', type: 'single', title: '设备', options: [{ id: 'desktop', label: '台式' }] },
    {
      id: 'A2',
      section: 'scene',
      type: 'multi',
      title: '用途',
      maxSelect: 2,
      options: [
        { id: 'web', label: '上网' },
        { id: 'dev', label: '开发' },
        { id: 'gaming', label: '游戏' },
      ],
    },
  ],
  dimensions: [],
}

const catalog = {
  software: [],
  softwareCategories: [],
  scenarios: [{ id: 'S1', title: '情景', type: 'single', options: [{ id: 'a', label: 'A' }] }],
  cli: [{ id: 'cli1', prompt: 'pwd', title: '做什么', options: [{ id: 'a', label: 'A' }] }],
  dimensions: [],
  groups: [],
  families: [],
  candidates: [],
}

describe('assessment store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    window.localStorage.clear()
  })

  it('loads quiz and catalog once', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const body = url.includes('/quiz') ? quiz : catalog
      return new Response(JSON.stringify(body), { status: 200 })
    })
    vi.stubGlobal('fetch', fetchMock)

    const store = useAssessmentStore()
    await store.ensureLoaded()
    await store.ensureLoaded()

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(store.questions).toHaveLength(2)
  })

  it('tracks completion and enforces multi-select limits', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) =>
        new Response(JSON.stringify(url.includes('/quiz') ? quiz : catalog), { status: 200 }),
      ),
    )
    const store = useAssessmentStore()
    await store.ensureLoaded()

    expect(store.quizComplete).toBe(false)

    store.toggleMulti('A2', 'web', 2)
    store.toggleMulti('A2', 'dev', 2)
    store.toggleMulti('A2', 'gaming', 2)
    // The third pick is rejected because maxSelect is two.
    expect(store.answers.A2).toEqual(['web', 'dev'])

    // Deselecting frees a slot.
    store.toggleMulti('A2', 'web', 2)
    store.toggleMulti('A2', 'gaming', 2)
    expect(store.answers.A2).toEqual(['dev', 'gaming'])

    store.setAnswer('A1', 'desktop')
    expect(store.quizComplete).toBe(true)
    expect(store.answeredCount).toBe(2)
  })

  it('submits, remembers history and exposes the result', async () => {
    const result = {
      sessionId: 'x',
      shareCode: 'abcd1234',
      createdAt: '2026-10-11T12:00:00+00:00',
      quizVersion: '1.0',
      radar: { labels: [], values: [] },
      profile: { dims: {}, weights: {}, traits: {} },
      top: [{ name: 'Pop!_OS', match: 71.5 }],
      full: [],
      families: [],
      requiredSoftware: [],
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url.includes('/assess')) return new Response(JSON.stringify(result), { status: 200 })
        return new Response(JSON.stringify(url.includes('/quiz') ? quiz : catalog), { status: 200 })
      }),
    )

    const store = useAssessmentStore()
    await store.ensureLoaded()
    store.begin()
    store.setAnswer('A1', 'desktop')

    const data = await store.submit()
    expect(data?.shareCode).toBe('abcd1234')
    expect(store.history[0]).toMatchObject({ shareCode: 'abcd1234', topName: 'Pop!_OS' })
    expect(JSON.parse(window.localStorage.getItem('syschoice.history') ?? '[]')).toHaveLength(1)

    store.reset()
    expect(store.answers).toEqual({})
    expect(store.result).toBeNull()
  })
})
