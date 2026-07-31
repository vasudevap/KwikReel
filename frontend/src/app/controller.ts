import {
  binClipOperation,
  clipPatchOperation,
  projectPatchOperation,
  rejectTrimOperation,
  relinkClipOperation,
  repairLinksOperation,
} from './operations.ts'
import { OptimisticProjectQueue } from './optimistic-queue.ts'
import { createSnapshot } from './state.ts'
import type {
  AppActions,
  AppClient,
  AppSnapshot,
  ClientLogInput,
  ClipPatchInput,
  ProjectPatchInput,
  ProjectWriteOperation,
  WriteOutcome,
} from './types.ts'

type Listener = () => void

export class AppController implements AppActions {
  readonly client: AppClient
  private snapshot: AppSnapshot
  private listeners = new Set<Listener>()
  private queue: OptimisticProjectQueue | null = null

  constructor(client: AppClient, initialSnapshot = createSnapshot()) {
    this.client = client
    this.snapshot = initialSnapshot
    if (initialSnapshot.project) this.installQueue(initialSnapshot)
  }

  getSnapshot = (): AppSnapshot => this.snapshot

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  async openProject(projectId: string): Promise<void> {
    const [project, log] = await Promise.all([
      this.client.getProject(projectId),
      this.client.getLog(projectId),
    ])
    const opened = createSnapshot({
      project,
      log,
      loadedSourceId: project.clips[0]?.source_id ?? null,
    })
    this.snapshot = opened
    this.installQueue(opened)
    this.emit()
    await this.repairLinks()
  }

  patchProject(patch: ProjectPatchInput): Promise<WriteOutcome> {
    const wasTrimmed = this.snapshot.project?.trim_assist_on === true
    const oldReverted = this.snapshot.trimWasReverted
    if (patch.trim_assist_on === false && wasTrimmed) {
      this.updateSnapshot({ trimWasReverted: true })
    } else if (patch.trim_assist_on === true) {
      this.updateSnapshot({ trimWasReverted: false })
    }
    return this.enqueue(projectPatchOperation(patch)).then((outcome) => {
      if (!outcome.ok) this.updateSnapshot({ trimWasReverted: oldReverted })
      return outcome
    })
  }

  patchClip(sourceId: string, patch: ClipPatchInput): Promise<WriteOutcome> {
    return this.enqueue(clipPatchOperation(sourceId, patch))
  }

  binClip(sourceId: string): Promise<WriteOutcome> {
    return this.enqueue(binClipOperation(sourceId))
  }

  rejectTrim(sourceId: string): Promise<WriteOutcome> {
    return this.enqueue(rejectTrimOperation(sourceId))
  }

  relinkClip(sourceId: string, path: string): Promise<WriteOutcome> {
    return this.enqueue(relinkClipOperation(sourceId, path))
  }

  repairLinks(): Promise<WriteOutcome> {
    return this.enqueue(repairLinksOperation())
  }

  enqueue(operation: ProjectWriteOperation): Promise<WriteOutcome> {
    if (this.queue) return this.queue.enqueue(operation)
    const error = new Error('No project is open.')
    this.appendFailure({
      kind: 'fault',
      text: 'Save failed: no project is open.',
      code: 'NO_PROJECT',
    })
    return Promise.resolve({
      ok: false,
      project: null,
      error,
    })
  }

  appendFailure(input: ClientLogInput): void {
    if (this.queue) {
      this.queue.recordFailure(input)
      return
    }
    const entry = {
      at: new Date().toISOString(),
      kind: input.kind,
      text: input.text,
      code: input.code ?? null,
      source_id: input.source_id ?? null,
      standing: false,
    } as const
    this.snapshot = createSnapshot({
      ...this.snapshot,
      log: [...this.snapshot.log, entry],
    })
    this.emit()
  }

  loadClip(sourceId: string | null): void {
    this.updateSnapshot({ loadedSourceId: sourceId })
  }

  setPlaying(playing: boolean): void {
    this.updateSnapshot({ playing })
  }

  private installQueue(snapshot: AppSnapshot): void {
    if (!snapshot.project) return
    this.queue = new OptimisticProjectQueue({
      client: this.client,
      project: snapshot.project,
      onProject: (project, pendingWrites) => {
        this.snapshot = createSnapshot({
          ...this.snapshot,
          project,
          pendingWrites,
        })
        this.emit()
      },
      onLog: (entry) => {
        this.snapshot = createSnapshot({
          ...this.snapshot,
          log: [...this.snapshot.log, entry],
        })
        this.emit()
      },
    })
  }

  private updateSnapshot(
    patch: Partial<
      Pick<AppSnapshot, 'loadedSourceId' | 'playing' | 'trimWasReverted'>
    >,
  ): void {
    this.snapshot = createSnapshot({ ...this.snapshot, ...patch })
    this.emit()
  }

  private emit(): void {
    for (const listener of this.listeners) listener()
  }

}
