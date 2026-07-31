import type { ComponentType } from 'react'

import type {
  AudioMix,
  AudioSettings,
  Music,
  Project,
  Segment,
  SpeedRange,
} from '../types/contracts.ts'

export const APP_VIEW_STATES = Object.freeze([
  'empty',
  'loaded',
  'trim-on',
  'trim-off',
  'speed-on',
  'playing',
] as const)

export type AppViewState = (typeof APP_VIEW_STATES)[number]

export interface LogEntry {
  at: string
  kind: 'info' | 'warn' | 'fault'
  text: string
  code: string | null
  source_id: string | null
  standing: boolean
}

export interface ApiErrorEnvelope {
  error_code: string
  human_text: string
  remediation: string
}

export interface CreateProjectInput {
  media_root: string
  output_resolution: Project['output_resolution']
  music_level: number
  clip_level: number
  target_duration_s?: number
  track_ref?: string | null
}

export type ProjectPatchInput = Partial<
  Pick<
    Project,
    | 'name'
    | 'target_duration_s'
    | 'output_resolution'
    | 'trim_assist_on'
    | 'speed_assist_on'
    | 'music'
  >
> & {
  audio?: AudioMix
}

export interface ClipPatchInput {
  order?: number
  segment?: Segment
  speed_ranges?: SpeedRange[]
  audio?: AudioSettings
}

export interface ClientLogInput {
  kind: 'warn' | 'fault'
  text: string
  code?: string | null
  source_id?: string | null
}

export interface JobRef {
  job_id: string
}

export interface JobStatus {
  state: 'queued' | 'running' | 'done' | 'error'
  progress: number
  error: string | null
}

export interface AppClient {
  pickFolder(): Promise<string | null>
  pickFile(): Promise<string | null>
  probeMusic(trackRef: string): Promise<Music>
  createProject(input: CreateProjectInput): Promise<Project>
  getProject(projectId: string): Promise<Project>
  patchProject(
    projectId: string,
    updatedAt: string,
    patch: ProjectPatchInput,
  ): Promise<Project>
  patchClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    patch: ClipPatchInput,
  ): Promise<Project>
  binClip(projectId: string, sourceId: string, updatedAt: string): Promise<Project>
  rejectTrim(projectId: string, sourceId: string, updatedAt: string): Promise<Project>
  relinkClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    path: string,
  ): Promise<Project>
  repairLinks(projectId: string, updatedAt: string): Promise<Project>
  getLog(projectId: string): Promise<LogEntry[]>
  appendClientLog(projectId: string, input: ClientLogInput): Promise<LogEntry>
  scan(projectId: string): Promise<JobRef>
  analyze(projectId: string): Promise<JobRef>
  proposeTrim(projectId: string, sourceIds?: string[]): Promise<JobRef>
  proposeSpeed(projectId: string, sourceIds?: string[]): Promise<JobRef>
  getJob(jobId: string): Promise<JobStatus>
  getClipPeaks(projectId: string, sourceId: string): Promise<number[]>
  getMusicPeaks(trackRef: string, contentHash: string): Promise<number[]>
  proxyUrl(sourceId: string): string
  thumbnailUrl(projectId: string, sourceId: string, atS?: number): string
  exportProject(projectId: string): Promise<JobRef>
  exportDownloadUrl(projectId: string): string
}

export interface AppSnapshot {
  view: AppViewState
  project: Project | null
  log: readonly LogEntry[]
  loadedSourceId: string | null
  previewQueueSourceIds: readonly string[]
  playing: boolean
  trimWasReverted: boolean
  pendingWrites: number
}

export interface ProjectWriteOperation {
  label: string
  optimistic(project: Project): Project
  commit(client: AppClient, project: Project): Promise<Project>
}

export interface WriteOutcome {
  ok: boolean
  project: Project | null
  error?: Error
}

export interface AppActions {
  patchProject(patch: ProjectPatchInput): Promise<WriteOutcome>
  patchClip(sourceId: string, patch: ClipPatchInput): Promise<WriteOutcome>
  binClip(sourceId: string): Promise<WriteOutcome>
  rejectTrim(sourceId: string): Promise<WriteOutcome>
  relinkClip(sourceId: string, path: string): Promise<WriteOutcome>
  repairLinks(): Promise<WriteOutcome>
  enqueue(operation: ProjectWriteOperation): Promise<WriteOutcome>
  appendFailure(input: ClientLogInput): void
  loadClip(sourceId: string | null): void
  togglePreviewQueue(sourceId: string): void
  setPlaying(playing: boolean): void
}

export interface AppModuleProps {
  snapshot: AppSnapshot
  client: AppClient
  actions: AppActions
}

export const MODULE_SLOT_NAMES = Object.freeze([
  'hud',
  'monitor',
  'reel',
  'transport',
  'sound',
  'editor',
  'index',
  'log',
] as const)

export type ModuleSlotName = (typeof MODULE_SLOT_NAMES)[number]
export type ModuleComponent = ComponentType<AppModuleProps>
export type ModuleSlots = Record<ModuleSlotName, ModuleComponent>
export type SlotProvider = Partial<ModuleSlots>
