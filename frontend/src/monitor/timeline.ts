import type {
  Clip,
  Project,
  Segment,
  SourceIndex,
  SpeedRange,
} from '../types/contracts.ts'

export interface PlaybackItem {
  sourceId: string
  name: string
  proxyUrl: string | null
  inS: number
  outS: number
  durationS: number
  fps: number
  width: number
  height: number
  speedRanges: readonly SpeedRange[]
}

function sourceFor(project: Project, sourceId: string): SourceIndex | null {
  return project.sources.find((source) => source.source_id === sourceId) ?? null
}

function clipFor(project: Project, sourceId: string): Clip | null {
  return project.clips.find((clip) => clip.source_id === sourceId) ?? null
}

function basename(path: string): string {
  const parts = path.split(/[\\/]/).filter(Boolean)
  return parts[parts.length - 1] ?? path
}

export function effectiveTrim(
  project: Project,
  clip: Clip,
  source: SourceIndex,
): Segment {
  if (clip.origin.segments === 'user' && clip.segment) return clip.segment
  const proposal = clip.proposals.segments
  if (
    project.trim_assist_on &&
    proposal &&
    proposal.disposition !== 'dismissed'
  ) {
    return proposal.value
  }
  return { in_s: 0, out_s: source.duration_s }
}

export function effectiveSpeed(
  project: Project,
  clip: Clip,
): readonly SpeedRange[] {
  if (clip.origin.speed === 'user') return clip.speed_ranges
  const proposal = clip.proposals.speed
  return project.speed_assist_on && proposal ? proposal.value : []
}

export function buildPlaybackQueue(
  project: Project | null,
  previewQueueSourceIds: readonly string[],
  proxyUrl: (sourceId: string) => string,
): readonly PlaybackItem[] {
  if (!project) return Object.freeze([])
  const items: PlaybackItem[] = []
  for (const sourceId of previewQueueSourceIds) {
    const source = sourceFor(project, sourceId)
    const clip = clipFor(project, sourceId)
    if (!source || !clip || !source.readable || !source.proxy_path) continue
    const trim = effectiveTrim(project, clip, source)
    const inS = Math.max(0, Math.min(trim.in_s, source.duration_s))
    const outS = Math.max(0, Math.min(trim.out_s, source.duration_s))
    if (outS <= inS) continue
    items.push({
      sourceId,
      name: basename(source.path),
      proxyUrl: source.path.startsWith('synthetic/') ? null : proxyUrl(sourceId),
      inS,
      outS,
      durationS: source.duration_s,
      fps: source.fps > 0 ? source.fps : 30,
      width: source.width,
      height: source.height,
      speedRanges: effectiveSpeed(project, clip),
    })
  }
  return Object.freeze(items)
}

export function playbackRateAt(
  item: PlaybackItem,
  sourceTimeS: number,
): number {
  const range = item.speedRanges.find(
    (candidate) =>
      sourceTimeS >= candidate.from_s && sourceTimeS < candidate.to_s,
  )
  return range?.rate && range.rate > 0 ? range.rate : 1
}

export function formatClock(seconds: number): string {
  const safe = Math.max(0, Math.floor(Number.isFinite(seconds) ? seconds : 0))
  return `${Math.floor(safe / 60)}:${String(safe % 60).padStart(2, '0')}`
}

export function recordedResolution(item: PlaybackItem | null): string {
  if (!item) return '—'
  const longEdge = Math.max(item.width, item.height)
  if (longEdge >= 3000) return '4K'
  if (longEdge >= 1600) return '1080P'
  return '720P'
}

export function scrubPercent(item: PlaybackItem | null, sourceTimeS: number): number {
  if (!item || item.durationS <= 0) return 0
  return Math.max(0, Math.min(100, (sourceTimeS / item.durationS) * 100))
}
