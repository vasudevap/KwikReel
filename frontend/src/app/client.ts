import type {
  AppClient,
  ApiErrorEnvelope,
  ClientLogInput,
  ClipPatchInput,
  CreateProjectInput,
  JobRef,
  JobStatus,
  LogEntry,
  ProjectPatchInput,
} from './types.ts'
import type { Music, Project } from '../types/contracts.ts'

export const CLIENT_METHODS = Object.freeze([
  'pickFolder',
  'pickFile',
  'probeMusic',
  'createProject',
  'getProject',
  'patchProject',
  'patchClip',
  'binClip',
  'rejectTrim',
  'relinkClip',
  'repairLinks',
  'getLog',
  'appendClientLog',
  'scan',
  'analyze',
  'proposeTrim',
  'proposeSpeed',
  'getJob',
  'getClipPeaks',
  'getMusicPeaks',
  'proxyUrl',
  'thumbnailUrl',
  'exportProject',
  'exportDownloadUrl',
] as const satisfies readonly (keyof AppClient)[])

export class ApiClientError extends Error {
  readonly status: number
  readonly envelope: ApiErrorEnvelope

  constructor(status: number, envelope: ApiErrorEnvelope) {
    super(envelope.human_text)
    this.name = 'ApiClientError'
    this.status = status
    this.envelope = envelope
  }

  get isConflict(): boolean {
    return this.status === 409
  }
}

type FetchLike = (
  input: string,
  init?: RequestInit,
) => Promise<Pick<Response, 'ok' | 'status' | 'json'>>

interface LiveClientOptions {
  capabilityToken: string
  baseUrl?: string
  fetch?: FetchLike
}

function path(baseUrl: string, route: string): string {
  return `${baseUrl.replace(/\/$/, '')}${route}`
}

function errorEnvelope(value: unknown): ApiErrorEnvelope {
  if (
    typeof value === 'object' &&
    value !== null &&
    'error_code' in value &&
    'human_text' in value &&
    'remediation' in value
  ) {
    return value as ApiErrorEnvelope
  }
  return {
    error_code: 'request_failed',
    human_text: 'The local request failed.',
    remediation: 'Try again. If it repeats, reopen the local app.',
  }
}

export class LiveClient implements AppClient {
  readonly baseUrl: string
  private readonly token: string
  private readonly fetcher: FetchLike

  constructor({
    capabilityToken,
    baseUrl = '',
    fetch: fetcher = globalThis.fetch.bind(globalThis),
  }: LiveClientOptions) {
    this.baseUrl = baseUrl
    this.token = capabilityToken
    this.fetcher = fetcher
  }

  private async request<T>(
    route: string,
    method: 'GET' | 'POST' | 'PATCH',
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = {}
    if (method !== 'GET') headers['x-capability-token'] = this.token
    if (body !== undefined) headers['content-type'] = 'application/json'
    const response = await this.fetcher(path(this.baseUrl, route), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
    const payload = await response.json()
    if (!response.ok) throw new ApiClientError(response.status, errorEnvelope(payload))
    return payload as T
  }

  async pickFolder(): Promise<string | null> {
    const result = await this.request<{ path: string | null }>('/api/pick-folder', 'POST')
    return result.path
  }

  async pickFile(): Promise<string | null> {
    const result = await this.request<{ path: string | null }>('/api/pick-file', 'POST')
    return result.path
  }

  probeMusic(trackRef: string): Promise<Music> {
    return this.request('/api/music/probe', 'POST', { track_ref: trackRef })
  }

  createProject(input: CreateProjectInput): Promise<Project> {
    return this.request('/api/project', 'POST', input)
  }

  getProject(projectId: string): Promise<Project> {
    return this.request(`/api/project/${encodeURIComponent(projectId)}`, 'GET')
  }

  patchProject(
    projectId: string,
    updatedAt: string,
    patch: ProjectPatchInput,
  ): Promise<Project> {
    return this.request(`/api/project/${encodeURIComponent(projectId)}`, 'PATCH', {
      updated_at: updatedAt,
      ...patch,
    })
  }

  patchClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    patch: ClipPatchInput,
  ): Promise<Project> {
    return this.request(
      `/api/project/${encodeURIComponent(projectId)}/clip/${encodeURIComponent(sourceId)}`,
      'PATCH',
      { updated_at: updatedAt, ...patch },
    )
  }

  binClip(projectId: string, sourceId: string, updatedAt: string): Promise<Project> {
    return this.request(
      `/api/project/${encodeURIComponent(projectId)}/clip/${encodeURIComponent(sourceId)}/bin`,
      'POST',
      { updated_at: updatedAt },
    )
  }

  rejectTrim(projectId: string, sourceId: string, updatedAt: string): Promise<Project> {
    return this.request(
      `/api/project/${encodeURIComponent(projectId)}/clip/${encodeURIComponent(sourceId)}/reject-trim`,
      'POST',
      { updated_at: updatedAt },
    )
  }

  relinkClip(
    projectId: string,
    sourceId: string,
    updatedAt: string,
    replacementPath: string,
  ): Promise<Project> {
    return this.request(
      `/api/project/${encodeURIComponent(projectId)}/relink/${encodeURIComponent(sourceId)}`,
      'POST',
      { updated_at: updatedAt, path: replacementPath },
    )
  }

  repairLinks(projectId: string, updatedAt: string): Promise<Project> {
    return this.request(
      `/api/project/${encodeURIComponent(projectId)}/repair-links`,
      'POST',
      { updated_at: updatedAt },
    )
  }

  getLog(projectId: string): Promise<LogEntry[]> {
    return this.request(`/api/project/${encodeURIComponent(projectId)}/log`, 'GET')
  }

  appendClientLog(projectId: string, input: ClientLogInput): Promise<LogEntry> {
    return this.request(`/api/project/${encodeURIComponent(projectId)}/log`, 'POST', input)
  }

  scan(projectId: string): Promise<JobRef> {
    return this.request(`/api/import/${encodeURIComponent(projectId)}/scan`, 'POST')
  }

  analyze(projectId: string): Promise<JobRef> {
    return this.request(`/api/analyze/${encodeURIComponent(projectId)}`, 'POST')
  }

  proposeTrim(projectId: string, sourceIds?: string[]): Promise<JobRef> {
    return this.request(`/api/propose/trim/${encodeURIComponent(projectId)}`, 'POST', {
      source_ids: sourceIds,
    })
  }

  proposeSpeed(projectId: string, sourceIds?: string[]): Promise<JobRef> {
    return this.request(`/api/propose/speed/${encodeURIComponent(projectId)}`, 'POST', {
      source_ids: sourceIds,
    })
  }

  getJob(jobId: string): Promise<JobStatus> {
    return this.request(`/api/jobs/${encodeURIComponent(jobId)}`, 'GET')
  }

  async getClipPeaks(projectId: string, sourceId: string): Promise<number[]> {
    const result = await this.request<{ peaks: number[] }>(
      `/api/media/peaks/${encodeURIComponent(projectId)}/${encodeURIComponent(sourceId)}`,
      'GET',
    )
    return result.peaks
  }

  async getMusicPeaks(trackRef: string, contentHash: string): Promise<number[]> {
    const query = new URLSearchParams({
      track_ref: trackRef,
      content_hash: contentHash,
    })
    const result = await this.request<{ peaks: number[] }>(
      `/api/music/peaks?${query.toString()}`,
      'GET',
    )
    return result.peaks
  }

  proxyUrl(sourceId: string): string {
    return path(this.baseUrl, `/api/media/proxy/${encodeURIComponent(sourceId)}`)
  }

  thumbnailUrl(projectId: string, sourceId: string, atS = 0): string {
    return path(
      this.baseUrl,
      `/api/media/thumb/${encodeURIComponent(projectId)}/${encodeURIComponent(sourceId)}?at_s=${encodeURIComponent(String(atS))}`,
    )
  }

  exportProject(projectId: string): Promise<JobRef> {
    return this.request(`/api/export/${encodeURIComponent(projectId)}`, 'POST')
  }

  exportDownloadUrl(projectId: string): string {
    return path(this.baseUrl, `/api/export/${encodeURIComponent(projectId)}/download`)
  }
}

export function createLiveClient(options: LiveClientOptions): AppClient {
  return new LiveClient(options)
}
