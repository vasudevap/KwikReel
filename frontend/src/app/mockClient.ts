// WO-107 · Mock client — an in-memory backend so the UI runs with no server.
// Mirrors the real contracts (contracts.ts) and job model; seeds a deliberately
// over-aggressive proposal so the trim-review screen actually gets exercised.

import type { AudioMode, CreateInput, JobStatus, ReelClient } from './client'
import type { Clip, Project, SourceIndex } from '../types/contracts'

const nowIso = () => new Date().toISOString()
const uid = () => 'mock-' + Math.floor(performance.now()).toString(36) + Math.floor(performance.now() % 997).toString(36)

function fullClip(source_id: string, order: number, included: boolean, dur: number): Clip {
  return {
    source_id,
    included,
    order,
    deleted: false,
    segments: [{ in_s: 0, out_s: dur, speed: [] }],
    audio: { retain: false, gain_db: 0 },
    origin: { included: included ? 'default' : 'default', order: 'default', segments: 'default', speed: 'default', audio: 'default' },
    proposals: { segments: null, included: null, order: null, speed: null },
  }
}

function seedSources(root: string): SourceIndex[] {
  const base = (name: string): Partial<SourceIndex> => ({ content_hash: 'sha256:' + name, path: `${root}/${name}`, has_gps: false })
  return [
    { source_id: 's1', duration_s: 12.4, captured_at: '2026-07-20T09:15:00-07:00', orientation: 'portrait', codec: 'hevc', fps: 30, width: 1080, height: 1920, has_audio: true, readable: true, proxy_path: null, ...base('IMG_0001.mov') } as SourceIndex,
    { source_id: 's2', duration_s: 9.0, captured_at: '2026-07-20T09:18:30-07:00', orientation: 'landscape', codec: 'h264', fps: 30, width: 1920, height: 1080, has_audio: false, readable: true, proxy_path: null, ...base('IMG_0002.mov') } as SourceIndex,
    { source_id: 's3', duration_s: 7.5, captured_at: '2026-07-20T09:24:10-07:00', orientation: 'portrait', codec: 'hevc', fps: 30, width: 1080, height: 1920, has_audio: true, readable: true, proxy_path: null, ...base('IMG_0003.mov') } as SourceIndex,
    { source_id: 's4', duration_s: 0, captured_at: null, orientation: 'portrait', codec: 'unknown', fps: 0, width: 0, height: 0, has_audio: false, readable: false, proxy_path: null, ...base('IMG_0004_corrupt.mov') } as SourceIndex,
  ]
}

// Deliberately varied proposals: a clean leading-blur trim, an over-aggressive one
// that cuts the good part (the reviewer should fix it), and a whole-clip keep.
function proposeFor(source: SourceIndex) {
  const dur = source.duration_s
  if (source.source_id === 's1') {
    return { seg: { in_s: 2.4, out_s: dur, speed: [] }, reasons: [{ code: 'LEADING_BLUR', human_text: `Trimmed the first 2.4 s — too blurry to keep (blur 0.14 vs 0.35 floor).`, evidence_refs: ['signals.blur[0:2]'], score: 0.14, confidence: 'high' as const }] }
  }
  if (source.source_id === 's2') {
    return { seg: { in_s: 6.5, out_s: 8.0, speed: [] }, reasons: [{ code: 'TRAILING_SHAKE', human_text: `Kept only the last 1.5 s — flagged the rest as shaky (shake 0.55 vs 0.50 limit).`, evidence_refs: ['signals.shake[0:6]'], score: 0.55, confidence: 'low' as const }] }
  }
  return { seg: { in_s: 0, out_s: dur, speed: [] }, reasons: [{ code: 'WHOLE_CLIP_GOOD', human_text: 'The whole clip cleared the quality floors — nothing needed trimming.', evidence_refs: [`signals.blur[0:${Math.round(dur)}]`], score: 0.72, confidence: 'high' as const }] }
}

export function createMockClient(): ReelClient {
  const projects = new Map<string, Project>()
  const jobs = new Map<string, JobStatus>()
  const clone = <T>(x: T): T => JSON.parse(JSON.stringify(x))

  function runJob(work: () => void): string {
    const id = uid()
    jobs.set(id, { state: 'running', progress: 0, error: null })
    let p = 0
    const timer = setInterval(() => {
      p += 0.25
      if (p >= 1) {
        clearInterval(timer)
        try {
          work()
          jobs.set(id, { state: 'done', progress: 1, error: null })
        } catch (e) {
          jobs.set(id, { state: 'error', progress: 1, error: String(e) })
        }
      } else {
        jobs.set(id, { state: 'running', progress: p, error: null })
      }
    }, 200)
    return id
  }

  const save = (p: Project): Project => {
    const saved = { ...clone(p), updated_at: nowIso() }
    projects.set(saved.project_id, saved)
    return clone(saved)
  }

  return {
    mode: 'mock',
    async createProject(input: CreateInput) {
      const id = uid()
      const now = nowIso()
      const project: Project = {
        schema_version: 1, project_id: id, created_at: now, updated_at: now, app_version: '0.1.0',
        name: input.media_root.split('/').pop() || 'Untitled', media_root: input.media_root, target_duration_s: input.target_duration_s,
        music: { track_ref: input.track_ref, content_hash: '', duration_s: 0, beats_s: [], sections: [] },
        sources: [], clips: [], stage_approvals: { ingest: null, trim: null, selection: null, speed: null, finalize: null },
        export: { audio_modes: ['music', 'clip', 'silent'], last_render: {} },
      }
      return save(project)
    },
    async getProject(id) { return clone(projects.get(id)!) },
    async saveProject(p) { return save(p) },
    async approve(id, stage) {
      const p = clone(projects.get(id)!)
      ;(p.stage_approvals as unknown as Record<string, string | null>)[stage] = nowIso()
      if (stage === 'trim') {
        for (const c of p.clips) {
          if (c.proposals.segments && c.proposals.segments.disposition === 'pending' && c.origin.segments === 'proposed') {
            c.proposals.segments.disposition = 'accepted'
          }
        }
      }
      return save(p)
    },
    scan(id) {
      return Promise.resolve(runJob(() => {
        const p = projects.get(id)!
        const sources = seedSources(p.media_root)
        const ordered = [...sources].sort((a, b) => (a.captured_at || '').localeCompare(b.captured_at || ''))
        p.sources = sources
        p.clips = ordered.map((s, i) => fullClip(s.source_id, i + 1, s.readable, s.duration_s))
        p.stage_approvals.ingest = nowIso()
      }))
    },
    analyze(id) { return Promise.resolve(runJob(() => { void projects.get(id) })) },
    propose(id, sourceIds) {
      return Promise.resolve(runJob(() => {
        const p = projects.get(id)!
        const wanted = sourceIds ? new Set(sourceIds) : null
        for (const c of p.clips) {
          const src = p.sources.find((s) => s.source_id === c.source_id)
          if (!src || !src.readable || !c.included || c.deleted) continue
          if (wanted && !wanted.has(c.source_id)) continue
          const { seg, reasons } = proposeFor(src)
          c.segments = [seg]
          c.origin.segments = 'proposed'
          c.proposals.segments = { value: [seg], at: nowIso(), reasons, disposition: 'pending' }
        }
      }))
    },
    finalize(id) { return Promise.resolve(runJob(() => { void projects.get(id) })) },
    export(id, mode: AudioMode) {
      return Promise.resolve(runJob(() => {
        const p = projects.get(id)!
        p.export.last_render[mode] = { path: `mock://${id}/${mode}.mp4`, rendered_at: nowIso(), qa: null }
      }))
    },
    async jobStatus(jobId) { return jobs.get(jobId) ?? { state: 'error', progress: 0, error: 'unknown job' } },
    proxyUrl: () => '',
    draftUrl: () => '',
    downloadUrl: () => '#',
  }
}
