// WO-107 · Live client — talks to the real FastAPI backend (ES-001 §6).
// The per-launch capability token (ADR-011) is injected into index.html by the
// server at page-serve time as window.__REEL_TOKEN__; mutations send it.

import type { AudioMode, CreateInput, JobStatus, Project, ReelClient } from './client'

const TOKEN: string = (globalThis as { __REEL_TOKEN__?: string }).__REEL_TOKEN__ ?? ''

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (method !== 'GET') headers['X-Capability-Token'] = TOKEN
  const res = await fetch('/api' + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = (data as { human_text?: string }).human_text ?? `Request failed (${res.status})`
    throw new Error(msg)
  }
  return data as T
}

export function createLiveClient(): ReelClient {
  return {
    mode: 'live',
    createProject: (input: CreateInput) => req<Project>('POST', '/project', input),
    getProject: (id) => req<Project>('GET', `/project/${id}`),
    saveProject: (p) => req<Project>('PUT', `/project/${p.project_id}`, p),
    approve: (id, stage) => req<Project>('POST', `/project/${id}/approve/${stage}`),
    scan: (id) => req<{ job_id: string }>('POST', `/import/${id}/scan`).then((r) => r.job_id),
    analyze: (id) => req<{ job_id: string }>('POST', `/analyze/${id}`).then((r) => r.job_id),
    propose: (id, sourceIds) =>
      req<{ job_id: string }>('POST', `/propose/trim/${id}`, { source_ids: sourceIds ?? null }).then((r) => r.job_id),
    finalize: (id) => req<{ job_id: string }>('POST', `/render/${id}/finalize`).then((r) => r.job_id),
    export: (id, mode: AudioMode) =>
      req<{ job_id: string }>('POST', `/export/${id}`, { audio_mode: mode }).then((r) => r.job_id),
    jobStatus: (jobId) => req<JobStatus>('GET', `/jobs/${jobId}`),
    proxyUrl: (sourceId) => `/api/media/proxy/${sourceId}`,
    draftUrl: (id) => `/api/render/${id}/draft`,
    downloadUrl: (id, mode) => `/api/export/${id}/download/${mode}`,
  }
}
