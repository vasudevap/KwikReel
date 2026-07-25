// WO-107 · The seam that lets the UI run on fake data or the real backend with
// no component change. Components depend on ReelClient; main.tsx picks live vs mock.

import type { Export, Project } from '../types/contracts'

export type { Project } from '../types/contracts'
// The audio-mode set, derived from the contract (drift-proof).
export type AudioMode = Export['audio_modes'][number]

export interface JobStatus {
  state: 'queued' | 'running' | 'done' | 'error'
  progress: number
  error: string | null
}

export interface CreateInput {
  media_root: string
  track_ref: string
  target_duration_s: number
}

/** The whole backend surface (ES-001 §6) the frontend needs, mode-agnostic. */
export interface ReelClient {
  readonly mode: 'mock' | 'live'
  createProject(input: CreateInput): Promise<Project>
  getProject(id: string): Promise<Project>
  saveProject(project: Project): Promise<Project>
  approve(id: string, stage: string): Promise<Project>
  scan(id: string): Promise<string> // -> job_id
  analyze(id: string): Promise<string>
  propose(id: string, sourceIds?: string[]): Promise<string>
  finalize(id: string): Promise<string>
  export(id: string, mode: AudioMode): Promise<string>
  jobStatus(jobId: string): Promise<JobStatus>
  proxyUrl(sourceId: string): string
  draftUrl(id: string): string
  downloadUrl(id: string, mode: AudioMode): string
}
