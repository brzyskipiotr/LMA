export interface Evidence {
  page_no: number
  snippet: string
}

export interface ExtractedFact {
  field: string
  value: string | number | null
  unit: string | null
  confidence: number
  evidence: Evidence[]
}

export interface VerificationResult {
  check_id: string
  check_type: string
  inputs: Record<string, unknown>
  result: string
  delta_pct: number | null
  why: string
  pages_to_verify: number[]
}

export interface RedFlag {
  flag_id: string
  severity: string
  category: string
  title: string
  description: string
  pages_to_verify: number[]
  recommended_action: string
}

export interface ScoreCard {
  evidence_coverage: number
  consistency: number
  feasibility: number
  traffic_light: string
  pages_to_verify: number[]
  missing_data: string[]
}

export interface PageInfo {
  page_no: number
  has_text: boolean
  char_count: number
}

export interface DocumentMeta {
  doc_id: string
  filename: string
  sha256: string
  pages: number
  created_at: string
}

export interface AnalysisReport {
  document: DocumentMeta
  page_info: PageInfo[]
  facts: ExtractedFact[]
  verifications: VerificationResult[]
  red_flags: RedFlag[]
  scorecard: ScoreCard
}
