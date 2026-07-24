// Seeded fake data for WO-100. Deliberately includes bad AI proposals (ADR-008
// rule 2) so the review screen actually gets exercised — reviewing is the
// product. All thumbnails are synthetic (ADR-013). Signals are representative,
// and every ReasonRecord cites the range that "drove" it (§4.4 transparency).
import type {
  Analysis,
  Clip,
  Orientation,
  Project,
  ReasonRecord,
  Segment,
  SegmentsProposal,
  SourceIndex,
} from './types'

const SHARP_FLOOR = 0.35

type Kind = 'good-head' | 'good-tail' | 'good-both' | 'bad-cuts-good' | 'giveup'

interface Seed {
  label: string
  secs: number
  when: string | null
  orient: Orientation
  audio: boolean
  gps: boolean
  readable?: boolean
  dup?: string
  kind: Kind
  note?: string // what the reviewer should notice (for bad proposals)
}

// A day at the beach, captured_at ascending. Two proposals are deliberately
// wrong: "Birthday candles" (cuts the good middle) and "Sunset B" (same).
// "Ferry ride" is the proposer giving up (full-clip fallback).
const SEEDS: Seed[] = [
  { label: 'Beach arrival', secs: 14, when: '2026-07-12T09:12:04-07:00', orient: 'portrait', audio: true, gps: false, kind: 'good-head' },
  { label: 'Sandcastle', secs: 22, when: '2026-07-12T09:41:22-07:00', orient: 'portrait', audio: true, gps: false, kind: 'good-tail' },
  { label: 'Wave jump', secs: 18, when: '2026-07-12T10:03:47-07:00', orient: 'portrait', audio: true, gps: false, kind: 'good-both' },
  { label: 'Birthday candles', secs: 13, when: '2026-07-12T10:31:10-07:00', orient: 'portrait', audio: true, gps: false, kind: 'bad-cuts-good', note: 'The candle blow-out is at ~6 s; the proposal keeps the boring sharp intro and cuts it.' },
  { label: 'Ferry ride', secs: 9, when: '2026-07-12T11:02:55-07:00', orient: 'landscape', audio: true, gps: false, kind: 'giveup' },
  { label: 'Ice cream', secs: 11, when: '2026-07-12T11:20:31-07:00', orient: 'portrait', audio: true, gps: false, kind: 'good-head' },
  { label: 'Pool splash', secs: 26, when: '2026-07-12T12:15:08-07:00', orient: 'portrait', audio: false, gps: false, kind: 'good-both', note: 'No audio track — exercises the silent-pad path in clip-audio mode.' },
  { label: 'Sunset A', secs: 31, when: '2026-07-12T19:44:19-07:00', orient: 'landscape', audio: true, gps: true, dup: 'dup-sunset', kind: 'good-tail' },
  { label: 'Sunset B', secs: 12, when: '2026-07-12T19:46:02-07:00', orient: 'landscape', audio: true, gps: true, dup: 'dup-sunset', kind: 'bad-cuts-good', note: 'Near-duplicate of Sunset A; proposal also cuts the best moment.' },
  { label: 'Corrupt clip', secs: 0, when: '2026-07-12T20:01:00-07:00', orient: 'portrait', audio: false, gps: false, readable: false, kind: 'giveup' },
]

function series(n: number, fn: (i: number) => number): number[] {
  return Array.from({ length: Math.max(0, Math.round(n)) }, (_, i) => Number(fn(i).toFixed(3)))
}
function reason(
  code: string,
  human_text: string,
  evidence_refs: string[],
  score: number,
  confidence: ReasonRecord['confidence'],
): ReasonRecord {
  return { code, human_text, evidence_refs, score, confidence }
}

interface Built {
  source: SourceIndex
  analysis: Analysis
  latent: SegmentsProposal | null // what the AI will propose when invoked
}

function build(seed: Seed, i: number): Built {
  const id = `src-${String(i + 1).padStart(2, '0')}`
  const secs = seed.secs
  const readable = seed.readable !== false
  const source: SourceIndex = {
    source_id: id,
    content_hash: `sha256:${id}-${seed.label.replace(/\s+/g, '').toLowerCase()}`,
    path: `/Users/owner/Movies/Beach Day/${seed.label.replace(/\s+/g, '_')}.mov`,
    duration_s: secs,
    captured_at: seed.when,
    orientation: seed.orient,
    codec: seed.orient === 'landscape' ? 'h264' : 'hevc',
    fps: 30,
    width: seed.orient === 'landscape' ? 1920 : 1080,
    height: seed.orient === 'landscape' ? 1080 : 1920,
    has_audio: seed.audio,
    has_gps: seed.gps,
    readable,
    proxy_path: `proxies/${id}.mp4`,
  }

  if (!readable) {
    // Unreadable: surfaced, never silently dropped. No analysis, no proposal.
    const analysis: Analysis = {
      source_id: id,
      signals: { blur: [], exposure: [], shake: [], motion_energy: [], audio_rms: [], people_count: null, saliency_ref: null },
      scene_cuts_s: [],
      dup_group: seed.dup ?? null,
      run_id: 'run-fake',
    }
    return { source, analysis, latent: null }
  }

  const head = Math.min(2.5, secs * 0.2)
  const tail = Math.min(3, secs * 0.2)
  const sharp = (i2: number) => {
    const t = i2 + 0.5
    if (seed.kind === 'giveup') return 0.18 + 0.04 * Math.sin(i2) // never clears floor
    if (seed.kind === 'bad-cuts-good') {
      // sharp-but-boring intro, then a bright good middle that the proposal drops
      if (t < 4) return 0.55
      if (t >= 5 && t <= secs - 2) return 0.62
      return 0.5
    }
    const blurryHead = (seed.kind === 'good-head' || seed.kind === 'good-both') && t < head
    return blurryHead ? 0.12 : 0.6
  }
  const motion = (i2: number) => {
    const t = i2 + 0.5
    const staticTail = (seed.kind === 'good-tail' || seed.kind === 'good-both') && t > secs - tail
    return staticTail ? 0.05 : 0.4
  }
  const audioRms = (i2: number) => {
    if (!seed.audio) return 0
    const t = i2 + 0.5
    const staticTail = (seed.kind === 'good-tail' || seed.kind === 'good-both') && t > secs - tail
    return staticTail ? 0.02 : 0.3
  }

  const analysis: Analysis = {
    source_id: id,
    signals: {
      blur: series(secs, sharp),
      exposure: series(secs, () => 0.1),
      shake: series(secs, (i2) => ((seed.kind === 'good-head' || seed.kind === 'good-both') && i2 + 0.5 < head ? 0.7 : 0.15)),
      motion_energy: series(secs, motion),
      audio_rms: series(secs, audioRms),
      people_count: null,
      saliency_ref: null,
    },
    scene_cuts_s: [],
    dup_group: seed.dup ?? null,
    run_id: 'run-fake',
  }

  // Build the latent proposal (what "AI trim" reveals when the user runs it).
  const seg = (in_s: number, out_s: number): Segment => ({ in_s, out_s, speed: [] })
  let value: Segment[]
  let reasons: ReasonRecord[]
  switch (seed.kind) {
    case 'good-head':
      value = [seg(round(head), secs)]
      reasons = [reason('LEADING_BLUR', `Trimmed the first ${fmt(head)} s — too blurry and shaky to keep (sharpness 0.12 vs ${SHARP_FLOOR} floor).`, [`signals.blur[0:${Math.ceil(head)}]`, `signals.shake[0:${Math.ceil(head)}]`], 0.12, 'high')]
      break
    case 'good-tail':
      value = [seg(0, round(secs - tail))]
      reasons = [reason('TRAILING_STATIC', `Trimmed the last ${fmt(tail)} s — dead air at the end (motion 0.05, audio 0.02).`, [`signals.motion_energy[${Math.floor(secs - tail)}:${secs}]`, `signals.audio_rms[${Math.floor(secs - tail)}:${secs}]`], 0.05, 'high')]
      break
    case 'good-both':
      value = [seg(round(head), round(secs - tail))]
      reasons = [
        reason('LEADING_BLUR', `Trimmed the first ${fmt(head)} s — blurry start (sharpness 0.12 vs ${SHARP_FLOOR} floor).`, [`signals.blur[0:${Math.ceil(head)}]`], 0.12, 'high'),
        reason('TRAILING_STATIC', `Trimmed the last ${fmt(tail)} s — static, quiet tail.`, [`signals.motion_energy[${Math.floor(secs - tail)}:${secs}]`], 0.05, 'med'),
      ]
      break
    case 'bad-cuts-good':
      // DELIBERATELY WRONG: keeps the sharp-but-boring intro, drops the good middle.
      value = [seg(0, 3.5)]
      reasons = [reason('KEPT_SHARPEST', `Kept the sharpest 3.5 s window at the start (sharpness 0.55).`, ['signals.blur[0:4]'], 0.55, 'med')]
      break
    case 'giveup':
      // Proposer gives up: nothing clears the floor -> propose the full clip, and say so.
      value = [seg(0, secs)]
      reasons = [reason('NO_CLEAR_WINDOW', `Nothing cleared the sharpness floor (${SHARP_FLOOR}); kept the whole clip so you can decide.`, [`signals.blur[0:${secs}]`], 0.18, 'low')]
      break
  }
  const latent: SegmentsProposal = { value, at: '2026-07-12T20:05:00-07:00', reasons, disposition: 'pending' }
  return { source, analysis, latent }
}

function round(x: number): number {
  return Number(x.toFixed(1))
}
function fmt(x: number): string {
  return x.toFixed(1)
}

export interface SeedData {
  project: Project
  analyses: Record<string, Analysis>
  latent: Record<string, SegmentsProposal>
}

export function buildSeedProject(name: string, mediaRoot: string, trackName: string): SeedData {
  const built = SEEDS.map(build)
  const analyses: Record<string, Analysis> = {}
  const latent: Record<string, SegmentsProposal> = {}

  const clips: Clip[] = built.map((b, i) => {
    analyses[b.source.source_id] = b.analysis
    if (b.latent) latent[b.source.source_id] = b.latent
    const readable = b.source.readable
    return {
      source_id: b.source.source_id,
      included: readable, // unreadable defaults excluded (cannot render); see gap list
      order: i + 1,
      deleted: false,
      segments: [{ in_s: 0, out_s: b.source.duration_s, speed: [] }], // default full clip
      audio: { retain: false, gain_db: 0 },
      // Gap: origin.segments has no value for the untouched default full clip
      // (schema allows only proposed|user). Defaulting to "user" pending §4 fix.
      origin: { included: 'user', order: 'user', segments: 'user', speed: 'user', audio: 'user' },
      proposals: { segments: null, included: null, order: null, speed: null },
    }
  })

  const project: Project = {
    schema_version: 1,
    project_id: 'proto-0001',
    created_at: '2026-07-24T00:00:00Z',
    updated_at: '2026-07-24T00:00:00Z',
    app_version: '0.1.0-proto',
    media_root: mediaRoot,
    target_duration_s: 75,
    music: {
      track_ref: `/Users/owner/Music/${trackName}.m4a`,
      content_hash: 'sha256:track-fake',
      duration_s: 191.4,
      beats_s: [],
      sections: [],
    },
    sources: built.map((b) => b.source),
    clips,
    stage_approvals: { ingest: null, trim: null, selection: null, speed: null, finalize: null },
    export: { audio_modes: [], last_render: null },
  }
  // Name is display-only in the prototype; ES-001 §4.1 has no project name field (gap).
  void name
  return { project, analyses, latent }
}
