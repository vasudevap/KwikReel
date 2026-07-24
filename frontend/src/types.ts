// Mirrors ES-001 §4 frozen schemas. The prototype runs on fake data, but the
// shapes track the real contract so the WO-100 -> WO-101 schema-gap list is
// grounded in what the screen actually needs. Where the screen needs something
// ES-001 §4 does not express, it goes in the gap list — never silently added.

export type Origin = 'proposed' | 'user'
export type Disposition = 'pending' | 'accepted' | 'adjusted' | 'dismissed'
export type Confidence = 'high' | 'med' | 'low'
export type AudioMode = 'music' | 'clip' | 'silent'
export type Orientation = 'portrait' | 'landscape'

export interface SpeedRamp { from_s: number; to_s: number; rate: number }
export interface Segment { in_s: number; out_s: number; speed: SpeedRamp[] }

// ES-001 §4.4 — the transparency primitive.
export interface ReasonRecord {
  code: string
  human_text: string
  evidence_refs: string[]
  score: number
  confidence: Confidence
}

export interface SegmentsProposal {
  value: Segment[]
  at: string
  reasons: ReasonRecord[]
  disposition: Disposition
}

export interface Proposals {
  segments: SegmentsProposal | null
  included: null // M2
  order: null // M2
  speed: null // M3
}

export interface ClipOrigin {
  included: Origin
  order: Origin
  segments: Origin
  speed: Origin
  audio: Origin
}

export interface Clip {
  source_id: string
  included: boolean
  order: number
  deleted: boolean
  segments: Segment[] // effective value — what renders
  audio: { retain: boolean; gain_db: number }
  origin: ClipOrigin
  proposals: Proposals
}

// ES-001 §4.2 — immutable facts.
export interface SourceIndex {
  source_id: string
  content_hash: string
  path: string
  duration_s: number
  captured_at: string | null
  orientation: Orientation
  codec: string
  fps: number
  width: number
  height: number
  has_audio: boolean
  has_gps: boolean // presence flag only; coordinates never enter project.json
  readable: boolean // false -> surfaced to the user, never silently dropped
  proxy_path: string
}

// ES-001 §4.3 — facts, not decisions.
export interface AnalysisSignals {
  blur: number[] // per-second sharpness (higher = sharper); floor applied in §5.2
  exposure: number[]
  shake: number[]
  motion_energy: number[]
  audio_rms: number[]
  people_count: null // M2 — COUNT ONLY when it arrives; identity never
  saliency_ref: null // deferred
}
export interface Analysis {
  source_id: string
  signals: AnalysisSignals
  scene_cuts_s: number[]
  dup_group: string | null
  run_id: string
}

export interface StageApprovals {
  ingest: string | null
  trim: string | null // LIVE in M1
  selection: string | null // M2 — inert
  speed: string | null // M3 — inert
  finalize: string | null
}

export interface Music {
  track_ref: string
  content_hash: string
  duration_s: number
  beats_s: number[]
  sections: unknown[]
}

export interface LastRender {
  path: string
  audio_mode: AudioMode
  rendered_at: string
  qa: { passed: boolean; notes: string[] }
}

// ES-001 §4.1 — canonical editor state (the real thing is one file on disk).
export interface Project {
  schema_version: 1
  project_id: string
  created_at: string
  updated_at: string
  app_version: string
  media_root: string
  target_duration_s: number
  music: Music | null
  sources: SourceIndex[]
  clips: Clip[]
  stage_approvals: StageApprovals
  export: {
    audio_modes: AudioMode[]
    last_render: LastRender | null
  }
}
