// GENERATED FILE — DO NOT EDIT.
// Source of truth: backend/contracts/models.py (SPEC.md §3, accepted 2026-07-28).
// Regenerate with:  python -m backend.contracts.gen_types
// Drift is caught by tests/contracts/test_ts_in_sync.py.


export interface Analysis {
  source_id: string;
  signals: Signals;
  scene_cuts_s: number[];
  dup_group: string | null;
  run_id: string;
}

export interface AudioMix {
  music_level: number;
  clip_level: number;
}

export interface AudioSettings {
  retain: boolean;
  gain_db: number;
}

export interface Clip {
  source_id: string;
  order: number;
  segment: Segment | null;
  speed_ranges: SpeedRange[];
  stashed_segment: Segment | null;
  audio: AudioSettings;
  origin: Origin;
  proposals: Proposals;
}

export interface Export {
  last_render: RenderRecord | null;
}

export interface Music {
  track_ref: string;
  content_hash: string;
  duration_s: number;
  in_s: number;
}

export interface Origin {
  order: "default" | "proposed" | "user";
  segments: "default" | "proposed" | "user";
  speed: "default" | "proposed" | "user";
  audio: "default" | "proposed" | "user";
}

export interface Project {
  schema_version: 2;
  project_id: string;
  created_at: string;
  updated_at: string;
  app_version: string;
  name: string | null;
  media_root: string;
  target_duration_s: number;
  output_resolution: "720p" | "1080p" | "4k";
  trim_assist_on: boolean;
  speed_assist_on: boolean;
  audio: AudioMix;
  music: Music | null;
  sources: SourceIndex[];
  clips: Clip[];
  export: Export;
}

export interface Proposals {
  segments: SegmentsProposal | null;
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
}

export interface SegmentsProposal {
  value: Segment;
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
