// GENERATED FILE — DO NOT EDIT.
// Source of truth: backend/contracts/models.py (ES-001 §4, as amended §4.5).
// Regenerate with:  python -m backend.contracts.gen_types
// Drift is caught by tests/contracts/test_ts_in_sync.py.


export interface Analysis {
  source_id: string;
  signals: Signals;
  scene_cuts_s: number[];
  dup_group: string | null;
  run_id: string;
}

export interface AudioSettings {
  retain: boolean;
  gain_db: number;
}

export interface Clip {
  source_id: string;
  included: boolean;
  order: number;
  deleted: boolean;
  segments: Segment[];
  audio: AudioSettings;
  origin: Origin;
  proposals: Proposals;
}

export interface Export {
  audio_modes: ("music" | "clip" | "silent")[];
  last_render: { [key: string]: RenderRecord };
}

export interface IncludedProposal {
  value: boolean;
  at: string;
  reasons: ReasonRecord[];
  disposition: "pending" | "accepted" | "adjusted" | "dismissed";
}

export interface Music {
  track_ref: string;
  content_hash: string;
  duration_s: number;
  beats_s: number[];
  sections: unknown[];
}

export interface OrderProposal {
  value: number;
  at: string;
  reasons: ReasonRecord[];
  disposition: "pending" | "accepted" | "adjusted" | "dismissed";
}

export interface Origin {
  included: "default" | "proposed" | "user";
  order: "default" | "proposed" | "user";
  segments: "default" | "proposed" | "user";
  speed: "default" | "proposed" | "user";
  audio: "default" | "proposed" | "user";
}

export interface Project {
  schema_version: 1;
  project_id: string;
  created_at: string;
  updated_at: string;
  app_version: string;
  name: string | null;
  media_root: string;
  target_duration_s: number;
  music: Music;
  sources: SourceIndex[];
  clips: Clip[];
  stage_approvals: StageApprovals;
  export: Export;
}

export interface Proposals {
  segments: SegmentsProposal | null;
  included: IncludedProposal | null;
  order: OrderProposal | null;
  speed: SpeedProposal | null;
}

export interface QAReport {
  passed: boolean;
  not_black: boolean;
  audio_ok: boolean;
  duration_ok: boolean;
  resolution_ok: boolean;
  codec_ok: boolean;
  safe_margins_ok: boolean;
  frame_count_ok: boolean;
  duration_s: number;
  width: number;
  height: number;
  reasons: string[];
}

export interface ReasonRecord {
  code: string;
  human_text: string;
  evidence_refs: string[];
  score: number;
  confidence: "high" | "med" | "low";
}

export interface RenderRecord {
  path: string;
  rendered_at: string;
  qa: QAReport | null;
}

export interface Segment {
  in_s: number;
  out_s: number;
  speed: SpeedRange[];
}

export interface SegmentsProposal {
  value: Segment[];
  at: string;
  reasons: ReasonRecord[];
  disposition: "pending" | "accepted" | "adjusted" | "dismissed";
}

export interface Signals {
  blur: number[];
  exposure: number[];
  shake: number[];
  motion_energy: number[];
  audio_rms: number[];
  people_count: number | null;
  saliency_ref: string | null;
}

export interface SourceIndex {
  source_id: string;
  content_hash: string;
  path: string;
  duration_s: number;
  captured_at: string | null;
  orientation: "portrait" | "landscape";
  codec: string;
  fps: number;
  width: number;
  height: number;
  has_audio: boolean;
  has_gps: boolean;
  readable: boolean;
  proxy_path: string | null;
}

export interface SpeedProposal {
  value: SpeedRange[];
  at: string;
  reasons: ReasonRecord[];
  disposition: "pending" | "accepted" | "adjusted" | "dismissed";
}

export interface SpeedRange {
  from_s: number;
  to_s: number;
  rate: number;
}

export interface StageApprovals {
  ingest: string | null;
  trim: string | null;
  selection: string | null;
  speed: string | null;
  finalize: string | null;
}
