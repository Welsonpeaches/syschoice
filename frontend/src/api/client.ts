import type {
  AdminSessionsResponse,
  AssessPayload,
  AssessResult,
  CatalogResponse,
  Feedback,
  InsightResponse,
  QuizResponse,
  StatsResponse,
} from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    })
  } catch {
    throw new ApiError('无法连接到服务器，请确认后端已启动。', 0)
  }

  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const body = await response.json()
      if (body?.error) message = body.error
    } catch {
      /* keep the default message */
    }
    throw new ApiError(message, response.status)
  }

  return (await response.json()) as T
}

export const api = {
  quiz: () => request<QuizResponse>('/quiz'),
  catalog: () => request<CatalogResponse>('/catalog'),
  assess: (payload: AssessPayload) =>
    request<AssessResult>('/assess', { method: 'POST', body: JSON.stringify(payload) }),
  result: (code: string) => request<AssessResult>(`/result/${code}`),
  insight: (code: string) =>
    request<InsightResponse>(`/result/${code}/insight`, { method: 'POST' }),
  sendFeedback: (
    code: string,
    payload: { chosenId?: string | null; satisfaction?: number | null; note?: string | null },
  ) =>
    request<{ ok: boolean; feedback: Feedback }>(`/result/${code}/feedback`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  stats: () => request<StatsResponse>('/stats'),
  adminSessions: (token: string, page: number, query: string) =>
    request<AdminSessionsResponse>(
      `/admin/sessions?page=${page}&pageSize=20&q=${encodeURIComponent(query)}`,
      { headers: { 'X-Admin-Token': token } },
    ),
  exportUrl: '/api/admin/export.csv',
}
