export type QuestionType = 'single' | 'multi' | 'scale'

export type Family = 'windows' | 'macos' | 'linux' | 'bsd'

export type CompatLevel = 'native' | 'good' | 'web' | 'partial' | 'none'

export interface Option {
  id: string
  label: string
  desc?: string
  value?: number
}

export interface Question {
  id: string
  section: string
  type: QuestionType
  title: string
  help?: string
  maxSelect?: number
  options: Option[]
}

export interface Section {
  id: string
  title: string
  desc: string
}

export interface Dimension {
  id: string
  label: string
  description?: string
  short?: string
}

export interface QuizResponse {
  version: string
  sections: Section[]
  questions: Question[]
  dimensions: Dimension[]
}

export interface SoftwareItem {
  id: string
  name: string
  category: string
  compat: Record<string, CompatLevel>
  note: string
}

export interface ScenarioQuestion {
  id: string
  title: string
  context?: string
  type: QuestionType
  options: Option[]
}

export interface CliQuestion {
  id: string
  prompt: string
  title: string
  options: Option[]
}

export interface CandidateSummary {
  id: string
  name: string
  family: Family
  group: string
  color: string
  monogram: string
  lineage: string
  blurb: string
}

export interface CatalogResponse {
  software: SoftwareItem[]
  softwareCategories: { id: string; label: string }[]
  scenarios: ScenarioQuestion[]
  cli: CliQuestion[]
  dimensions: Dimension[]
  groups: string[]
  families: { id: Family; label: string; color: string }[]
  candidates: CandidateSummary[]
}

export interface Note {
  type: 'match' | 'mismatch'
  text: string
}

export interface CandidateEntry {
  rank: number
  id: string
  name: string
  family: Family
  familyLabel: string
  familyColor: string
  group: string
  color: string
  monogram: string
  lineage: string
  blurb: string
  match: number
  pros: string[]
  cons: string[]
  dims: Record<string, number>
  notes: Note[]
}

export interface FamilySummary {
  family: Family
  label: string
  color: string
  average: number
  count: number
  best: { id: string; name: string; match: number } | null
}

export interface AssessResult {
  sessionId: string
  shareCode: string
  createdAt: string
  quizVersion: string
  llmEnabled?: boolean
  insight?: string | null
  insightModel?: string | null
  feedback?: Feedback | null
  radar: { labels: string[]; values: number[] }
  profile: {
    dims: Record<string, number>
    weights: Record<string, number>
    traits: Record<string, number | string>
  }
  top: CandidateEntry[]
  full: CandidateEntry[]
  families: FamilySummary[]
  requiredSoftware: string[]
}

export interface Feedback {
  id: string
  share_code: string
  created_at: string
  chosen_id: string | null
  chosen_name: string | null
  satisfaction: number | null
  note: string | null
}

export interface InsightResponse {
  insight: string
  model: string | null
  cached: boolean
}

export interface HardwareReading {
  cores?: number
  memoryGB?: number
  gpu?: string
  platform?: string
  vendor?: string
  devicePixelRatio?: number
  touchPoints?: number
  source?: string
}

export interface AssessPayload {
  answers: Record<string, string | string[] | number>
  scenarios: Record<string, string>
  cli: Record<string, string>
  software: string[]
  hardware: HardwareReading
  durationMs?: number
}

export interface StatsResponse {
  total: number
  averageMatch: number
  familyCount: number
  byFamily: { family: Family; count: number }[]
  topCandidates: {
    id: string
    name: string
    family: Family
    group: string
    count: number
    averageMatch: number
  }[]
  daily: { date: string; count: number }[]
  familyLabels: Record<string, string>
  familyColors: Record<string, string>
}

export interface AdminSessionRow {
  id: string
  share_code: string
  quiz_version: string
  created_at: string
  duration_ms: number | null
  top1_name: string | null
  top1_family: string | null
  top1_group: string | null
  top1_match: number | null
}

export interface AdminSessionsResponse {
  total: number
  page: number
  pageSize: number
  items: AdminSessionRow[]
}
