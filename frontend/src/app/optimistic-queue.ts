import { ApiClientError } from './client.ts'
import { cloneProject } from './state.ts'
import type {
  AppClient,
  ClientLogInput,
  LogEntry,
  ProjectWriteOperation,
  WriteOutcome,
} from './types.ts'
import type { Project } from '../types/contracts.ts'

interface PendingWrite {
  operation: ProjectWriteOperation
  resolve(outcome: WriteOutcome): void
}

interface OptimisticQueueOptions {
  client: AppClient
  project: Project
  onProject(project: Project, pendingWrites: number): void
  onLog(entry: LogEntry): void
  now?: () => string
}

const CONFLICT_FAILURE: ClientLogInput = {
  kind: 'fault',
  text: 'Save conflict: your change was reverted because the project changed elsewhere.',
  code: 'SAVE_CONFLICT',
}

const WRITE_FAILURE: ClientLogInput = {
  kind: 'fault',
  text: 'Save failed: your change was reverted. Check the local server and try again.',
  code: 'SAVE_FAILED',
}

function visibleEntry(input: ClientLogInput, at: string): LogEntry {
  return {
    at,
    kind: input.kind,
    text: input.text,
    code: input.code ?? null,
    source_id: input.source_id ?? null,
    standing: false,
  }
}

export class OptimisticProjectQueue {
  private readonly client: AppClient
  private readonly onProject: OptimisticQueueOptions['onProject']
  private readonly onLog: OptimisticQueueOptions['onLog']
  private readonly now: () => string
  private base: Project
  private pending: PendingWrite[] = []
  private bufferedFailures: ClientLogInput[] = []
  private draining = false

  constructor({
    client,
    project,
    onProject,
    onLog,
    now = () => new Date().toISOString(),
  }: OptimisticQueueOptions) {
    this.client = client
    this.base = cloneProject(project)
    this.onProject = onProject
    this.onLog = onLog
    this.now = now
  }

  get pendingCount(): number {
    return this.pending.length
  }

  replaceBase(project: Project): void {
    this.base = cloneProject(project)
    this.publish()
  }

  enqueue(operation: ProjectWriteOperation): Promise<WriteOutcome> {
    const outcome = new Promise<WriteOutcome>((resolve) => {
      this.pending.push({ operation, resolve })
    })
    this.publish()
    void this.drain()
    return outcome
  }

  recordFailure(input: ClientLogInput): void {
    this.onLog(visibleEntry(input, this.now()))
    void this.persistFailure(input)
  }

  async retryBufferedFailures(): Promise<void> {
    const buffered = this.bufferedFailures
    this.bufferedFailures = []
    for (const failure of buffered) {
      await this.persistFailure(failure)
    }
  }

  private renderedProject(): Project {
    return this.pending.reduce(
      (project, pending) => pending.operation.optimistic(project),
      cloneProject(this.base),
    )
  }

  private publish(): void {
    this.onProject(this.renderedProject(), this.pending.length)
  }

  private async drain(): Promise<void> {
    if (this.draining) return
    this.draining = true
    while (this.pending.length > 0) {
      const current = this.pending[0]
      try {
        const saved = await current.operation.commit(this.client, cloneProject(this.base))
        this.base = cloneProject(saved)
        this.pending.shift()
        this.publish()
        current.resolve({ ok: true, project: cloneProject(saved) })
        await this.retryBufferedFailures()
      } catch (caught) {
        const error = caught instanceof Error ? caught : new Error('local request failed')
        const conflict = error instanceof ApiClientError && error.isConflict
        if (conflict) {
          try {
            this.base = await this.client.getProject(this.base.project_id)
          } catch {
            // The known-good local base remains the rollback point when refresh fails.
          }
        }
        this.pending.shift()
        this.publish()
        const failure = conflict ? CONFLICT_FAILURE : WRITE_FAILURE
        this.recordFailure(failure)
        current.resolve({
          ok: false,
          project: cloneProject(this.base),
          error,
        })
      }
    }
    this.draining = false
  }

  private async persistFailure(input: ClientLogInput): Promise<void> {
    try {
      await this.client.appendClientLog(this.base.project_id, input)
    } catch {
      this.bufferedFailures.push(input)
    }
  }
}
