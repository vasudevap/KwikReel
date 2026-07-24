import type { SeedData } from './fixtures'
import type { Project } from './types'
import type { DemoSpeed } from './fakeAsync'

export type StageId = 'create' | 'sources' | 'ingest' | 'curate' | 'trim' | 'finalize' | 'export'

export interface StageProps {
  data: SeedData
  update: (fn: (p: Project) => Project) => void
  speed: DemoSpeed
  setSpeed: (s: DemoSpeed) => void
  goto: (s: StageId) => void
  projName: string
}
