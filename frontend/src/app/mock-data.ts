import type { Clip, Project, SourceIndex } from '../types/contracts.ts'
import { createSnapshot } from './state.ts'
import type { AppSnapshot, AppViewState, LogEntry } from './types.ts'

const MOCK_NOW = '2026-07-30T12:00:00Z'

function mockSource(
  sourceId: string,
  filename: string,
  durationS: number,
  order: number,
): SourceIndex {
  return {
    source_id: sourceId,
    content_hash: `synthetic-hash-${order}`,
    path: `synthetic/${filename}`,
    duration_s: durationS,
    captured_at: `2026-07-2${order}T10:00:00Z`,
    orientation: order % 2 === 0 ? 'landscape' : 'portrait',
    codec: 'h264',
    fps: 30,
    width: order % 2 === 0 ? 1920 : 1080,
    height: order % 2 === 0 ? 1080 : 1920,
    has_audio: true,
    has_gps: false,
    readable: true,
    proxy_path: `synthetic/proxy-${sourceId}.mp4`,
  }
}

function mockClip(sourceId: string, order: number, durationS: number): Clip {
  return {
    source_id: sourceId,
    order,
    segment: null,
    speed_ranges: [],
    stashed_segment: null,
    audio: { retain: true, gain_db: 0 },
    origin: {
      order: 'default',
      segments: 'proposed',
      speed: 'proposed',
      audio: 'default',
    },
    proposals: {
      segments: {
        value: { in_s: 0.4, out_s: durationS - 0.6 },
        at: MOCK_NOW,
        reasons: [
          {
            code: 'SYNTHETIC_TRIM',
            human_text: 'Synthetic quiet edges make a useful trim boundary.',
            evidence_refs: [],
            score: 0.7,
            confidence: 'med',
          },
        ],
        disposition: 'pending',
      },
      speed: {
        value: [{ from_s: 2, to_s: 4, rate: 1.5 }],
        at: MOCK_NOW,
        reasons: [
          {
            code: 'SYNTHETIC_SPEED',
            human_text: 'Synthetic motion and audio are both low here.',
            evidence_refs: [],
            score: 0.6,
            confidence: 'med',
          },
        ],
        disposition: 'pending',
      },
    },
  }
}

export function createMockProject(
  patch: Partial<Project> = {},
): Project {
  const sources = [
    mockSource('source-a', 'beach-walk.mp4', 12, 1),
    mockSource('source-b', 'wave-jump.mp4', 9, 2),
  ]
  const clips = [
    mockClip('source-a', 1, sources[0].duration_s),
    mockClip('source-b', 2, sources[1].duration_s),
  ]
  return {
    schema_version: 2,
    project_id: 'synthetic-project',
    created_at: MOCK_NOW,
    updated_at: MOCK_NOW,
    app_version: '0.2.0',
    name: 'Synthetic family day',
    media_root: 'synthetic/family-day',
    target_duration_s: 75,
    output_resolution: '1080p',
    trim_assist_on: false,
    speed_assist_on: false,
    audio: { music_level: 0.6, clip_level: 0.8 },
    music: null,
    sources,
    clips,
    export: { last_render: null },
    ...patch,
  }
}

export function createMockLog(): LogEntry[] {
  return [
    {
      at: MOCK_NOW,
      kind: 'info',
      text: 'Originals are opened read-only and never changed.',
      code: 'ORIGINALS_READ_ONLY',
      source_id: null,
      standing: true,
    },
    {
      at: MOCK_NOW,
      kind: 'info',
      text: 'Previews are made on this Mac. Nothing is uploaded and nobody is recognised.',
      code: 'LOCAL_ONLY',
      source_id: null,
      standing: true,
    },
  ]
}

export function mockSnapshotForView(view: AppViewState): AppSnapshot {
  if (view === 'empty') {
    return createSnapshot({ log: createMockLog(), previewQueueSourceIds: [] })
  }
  const project = createMockProject({
    trim_assist_on: view === 'trim-on' || view === 'speed-on' || view === 'playing',
    speed_assist_on: view === 'speed-on' || view === 'playing',
  })
  return createSnapshot({
    project,
    log: createMockLog(),
    loadedSourceId: project.clips[0]?.source_id ?? null,
    previewQueueSourceIds: project.clips.map((clip) => clip.source_id),
    playing: view === 'playing',
    trimWasReverted: view === 'trim-off',
  })
}
