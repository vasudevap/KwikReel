import { ApiClientError } from './client.ts'
import { cloneProject } from './state.ts'
import type {
  AppClient,
  ClientLogInput,
  ClipPatchInput,
  CreateProjectInput,
  JobRef,
  JobStatus,
  LogEntry,
  ProjectPatchInput,
} from './types.ts'
import type { Music, Project } from '../types/contracts.ts'

interface MockClientOptions {
  project?: Project | null
  log?: LogEntry[]
}

function conflictError(): ApiClientError {
  return new ApiClientError(409, {
    error_code: 'conflict',
    human_text: 'The project changed since you loaded it.',
    remediation: 'Reload, reapply your edit, and save again.',
  })
}

export class MockClient implements AppClient {
  readonly calls: string[] = []
  private project: Project | null
  private log: LogEntry[]
  private revision = 0
  private conflictPending = false

  constructor({ project = null, log = [] }: MockClientOptions = {}) {
    this.project = project ? cloneProject(project) : null
    this.log = log.map((entry) => ({ ...entry }))
  }

  conflictNextWrite(): void {
    this.conflictPending = true
  }

  private current(projectId?: string): Project {
    if (this.project === null || (projectId && this.project.project_id !== projectId)) {
      throw new ApiClientError(404, {
        error_code: 'not_found',
        human_text: 'No such synthetic project.',
        remediation: 'Create or open a project first.',
      })
    }
    return this.project
  }

  private save(project: Project): Project {
    this.revision += 1
    project.updated_at = `2026-07-30T12:00:${String(this.revision).padStart(2, '0')}Z`
    this.project = cloneProject(project)
    return cloneProject(project)
  }

  private requireCurrent(updatedAt: string): Project {
    const project = this.current()
    if (this.conflictPending) {
      this.conflictPending = false
      this.revision += 1
      project.updated_at = `2026-07-30T12:01:${String(this.revision).padStart(2, '0')}Z`
      this.project = cloneProject(project)
      throw conflictError()
    }
    if (project.updated_at !== updatedAt) throw conflictError()
    return cloneProject(project)
  }

  async pickFolder(): Promise<string | null> {
    this.calls.push('pickFolder')
    return 'synthetic/family-day'
  }

  async pickFile(): Promise<string | null> {
    this.calls.push('pickFile')
    return 'synthetic/music.wav'
  }

  async probeMusic(trackRef: string): Promise<Music> {
    this.calls.push('probeMusic')
    return {
      track_ref: trackRef,
      content_hash: 'synthetic-music-hash',
      duration_s: 120,
      in_s: 0,
    }
  }

  async createProject(input: CreateProjectInput): Promise<Project> {
    this.calls.push('createProject')
    const now = '2026-07-30T12:00:00Z'
    this.project = {
      schema_version: 2,
      project_id: 'synthetic-created-project',
      created_at: now,
      updated_at: now,
      app_version: '0.2.0',
      name: null,
      media_root: input.media_root,
      target_duration_s: input.target_duration_s ?? 75,
      output_resolution: input.output_resolution,
      trim_assist_on: false,
      speed_assist_on: false,
      audio: { music_level: input.music_level, clip_level: input.clip_level },
      music: null,
      sources: [],
      clips: [],
      export: { last_render: null },
    }
    return cloneProject(this.project)
  }

  async getProject(projectId: string): Promise<Project> {
    this.calls.push('getProject')
    return cloneProject(this.current(projectId))
  }

  async patchProject(
    projectId: string,
    updatedAt: string,
    patch: ProjectPatchInput,
  ): Promise<Project> {
    this.calls.push('patchProject')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    Object.assign(project, patch)
    return this.save(project)
  }

  async patchClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    patch: ClipPatchInput,
  ): Promise<Project> {
    this.calls.push('patchClip')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    const clip = project.clips.find((item) => item.source_id === sourceId)
    if (!clip) return this.current('missing')
    Object.assign(clip, patch)
    if (patch.segment !== undefined) clip.origin.segments = 'user'
    if (patch.speed_ranges !== undefined) clip.origin.speed = 'user'
    if (patch.audio !== undefined) clip.origin.audio = 'user'
    return this.save(project)
  }

  async binClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
  ): Promise<Project> {
    this.calls.push('binClip')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    const clip = project.clips.find((item) => item.source_id === sourceId)
    if (!clip) return this.current('missing')
    if (clip.stashed_segment) {
      clip.segment = clip.stashed_segment
      clip.stashed_segment = null
    } else {
      clip.stashed_segment = clip.segment ?? { in_s: 0, out_s: 0 }
      clip.segment = { in_s: 0, out_s: 0 }
    }
    clip.origin.segments = 'user'
    return this.save(project)
  }

  async rejectTrim(
    projectId: string,
    sourceId: string,
    updatedAt: string,
  ): Promise<Project> {
    this.calls.push('rejectTrim')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    const clip = project.clips.find((item) => item.source_id === sourceId)
    if (!clip?.proposals.segments) return this.current('missing')
    clip.proposals.segments.disposition = 'dismissed'
    return this.save(project)
  }

  async relinkClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    replacementPath: string,
  ): Promise<Project> {
    this.calls.push('relinkClip')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    const source = project.sources.find((item) => item.source_id === sourceId)
    if (!source) return this.current('missing')
    source.path = replacementPath
    return this.save(project)
  }

  async repairLinks(projectId: string, updatedAt: string): Promise<Project> {
    this.calls.push('repairLinks')
    const project = this.requireCurrent(updatedAt)
    if (project.project_id !== projectId) return this.current(projectId)
    return this.save(project)
  }

  async getLog(projectId: string): Promise<LogEntry[]> {
    this.calls.push('getLog')
    this.current(projectId)
    return this.log.map((entry) => ({ ...entry }))
  }

  async appendClientLog(projectId: string, input: ClientLogInput): Promise<LogEntry> {
    this.calls.push('appendClientLog')
    this.current(projectId)
    const entry: LogEntry = {
      at: `2026-07-30T12:02:${String(this.log.length).padStart(2, '0')}Z`,
      kind: input.kind,
      text: input.text,
      code: input.code ?? null,
      source_id: input.source_id ?? null,
      standing: false,
    }
    this.log.push(entry)
    return { ...entry }
  }

  private job(label: string): JobRef {
    this.calls.push(label)
    return { job_id: `synthetic-${label}` }
  }

  async scan(_projectId: string): Promise<JobRef> {
    return this.job('scan')
  }

  async analyze(_projectId: string): Promise<JobRef> {
    return this.job('analyze')
  }

  async proposeTrim(_projectId: string, _sourceIds?: string[]): Promise<JobRef> {
    return this.job('proposeTrim')
  }

  async proposeSpeed(_projectId: string, _sourceIds?: string[]): Promise<JobRef> {
    return this.job('proposeSpeed')
  }

  async getJob(_jobId: string): Promise<JobStatus> {
    this.calls.push('getJob')
    return { state: 'done', progress: 1, error: null }
  }

  async getClipPeaks(_projectId: string, _sourceId: string): Promise<number[]> {
    this.calls.push('getClipPeaks')
    return [0.1, 0.4, 0.2, 0.7]
  }

  async getMusicPeaks(_trackRef: string, _contentHash: string): Promise<number[]> {
    this.calls.push('getMusicPeaks')
    return [0.2, 0.5, 0.3, 0.6]
  }

  proxyUrl(sourceId: string): string {
    this.calls.push('proxyUrl')
    return `/api/media/proxy/${encodeURIComponent(sourceId)}`
  }

  thumbnailUrl(projectId: string, sourceId: string, atS = 0): string {
    this.calls.push('thumbnailUrl')
    return `/api/media/thumb/${encodeURIComponent(projectId)}/${encodeURIComponent(sourceId)}?at_s=${atS}`
  }

  async exportProject(_projectId: string): Promise<JobRef> {
    return this.job('exportProject')
  }

  exportDownloadUrl(projectId: string): string {
    this.calls.push('exportDownloadUrl')
    return `/api/export/${encodeURIComponent(projectId)}/download`
  }
}
