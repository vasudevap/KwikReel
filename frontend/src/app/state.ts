import type { Project } from '../types/contracts.ts'
import type { AppSnapshot, AppViewState, LogEntry } from './types.ts'

export interface ViewStateInput {
  project: Project | null
  playing: boolean
  trimWasReverted: boolean
}

export function deriveViewState({
  project,
  playing,
  trimWasReverted,
}: ViewStateInput): AppViewState {
  if (project === null) return 'empty'
  if (playing) return 'playing'
  if (project.speed_assist_on) return 'speed-on'
  if (project.trim_assist_on) return 'trim-on'
  if (trimWasReverted) return 'trim-off'
  return 'loaded'
}

export interface SnapshotInput {
  project?: Project | null
  log?: readonly LogEntry[]
  loadedSourceId?: string | null
  previewQueueSourceIds?: readonly string[]
  playing?: boolean
  trimWasReverted?: boolean
  pendingWrites?: number
}

export function normalizePreviewQueue(
  project: Project | null,
  sourceIds?: readonly string[],
): readonly string[] {
  if (!project) return Object.freeze([])
  const selected = sourceIds ? new Set(sourceIds) : null
  return Object.freeze(
    [...project.clips]
      .sort((left, right) => left.order - right.order)
      .filter((clip) => selected === null || selected.has(clip.source_id))
      .map((clip) => clip.source_id),
  )
}

export function createSnapshot(input: SnapshotInput = {}): AppSnapshot {
  const project = input.project ?? null
  const playing = input.playing ?? false
  const trimWasReverted = input.trimWasReverted ?? false
  return Object.freeze({
    view: deriveViewState({ project, playing, trimWasReverted }),
    project,
    log: Object.freeze([...(input.log ?? [])]),
    loadedSourceId: input.loadedSourceId ?? null,
    previewQueueSourceIds: normalizePreviewQueue(
      project,
      input.previewQueueSourceIds,
    ),
    playing,
    trimWasReverted,
    pendingWrites: input.pendingWrites ?? 0,
  })
}

export function cloneProject(project: Project): Project {
  return JSON.parse(JSON.stringify(project)) as Project
}

export function replaceProject(
  snapshot: AppSnapshot,
  project: Project | null,
  pendingWrites = snapshot.pendingWrites,
): AppSnapshot {
  return createSnapshot({
    ...snapshot,
    project,
    pendingWrites,
  })
}
