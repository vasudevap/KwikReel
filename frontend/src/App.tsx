import { useState } from 'react'
import type { StageId, StageProps } from './appTypes'
import type { Project } from './types'
import { buildSeedProject, type SeedData } from './fixtures'
import type { DemoSpeed } from './fakeAsync'
import { Stepper, type StepDef } from './ui'
import { CurateStage, IngestStage } from './stagesMid'
import { TrimStage } from './stagesTrim'
import { ExportStage, FinalizeStage } from './stagesEnd'

// The M1 walkable path. `selection` (M2) and `speed` (M3) are shown inert to
// keep the nine-stage / five-gate pipeline honest about what M1 actually runs.
const STEPS: StepDef[] = [
  { id: 'create', label: 'Create' },
  { id: 'sources', label: 'Sources' },
  { id: 'ingest', label: 'Import', gate: true },
  { id: 'selection', label: 'AI select', inert: true },
  { id: 'curate', label: 'Curate' },
  { id: 'trim', label: 'AI trim', gate: true },
  { id: 'speed', label: 'Speed', inert: true },
  { id: 'finalize', label: 'Finalize', gate: true },
  { id: 'export', label: 'Export' },
]

const FOLDERS = ['/Users/owner/Movies/Beach Day', '/Users/owner/Movies/Ski Trip 2026']
const TRACKS = ['Sunny Days (local)', 'Golden Hour (local)']

export function App() {
  const [data, setData] = useState<SeedData | null>(null)
  const [stage, setStage] = useState<StageId>('create')
  const [speed, setSpeed] = useState<DemoSpeed>('fast')
  const [projName, setProjName] = useState('Beach Day')
  const [mediaRoot, setMediaRoot] = useState(FOLDERS[0])
  const [track, setTrack] = useState(TRACKS[0])

  const update = (fn: (p: Project) => Project) => setData((d) => (d ? { ...d, project: fn(d.project) } : d))
  const goto = (s: StageId) => setStage(s)

  function startAnalysis() {
    setData(buildSeedProject(projName, mediaRoot, track))
    setStage('ingest')
  }

  const currentIdx = STEPS.findIndex((s) => s.id === stage)
  const doneIds = new Set(STEPS.filter((s, i) => i < currentIdx && !s.inert).map((s) => s.id))
  const stageProps: StageProps | null = data ? { data, update, speed, setSpeed, goto, projName } : null

  return (
    <>
      <div className="proto-banner">
        WO-100 clickable prototype — <strong>fake data</strong>, no real footage, no backend. Some AI
        proposals are wrong on purpose (ADR-008).
      </div>
      <div className="shell">
        <div className="row spread wrap">
          <h1 style={{ margin: 0 }}>
            🎬 Reel Agent <span className="muted small">— first-draft editor</span>
          </h1>
          {data && (
            <button
              onClick={() => {
                setData(null)
                setStage('create')
              }}
            >
              Start over
            </button>
          )}
        </div>
        <Stepper steps={STEPS} currentIdx={currentIdx} doneIds={doneIds} />

        {stage === 'create' && (
          <div className="panel">
            <h2>New project</h2>
            <div className="row wrap">
              <label>
                Name <input value={projName} onChange={(e) => setProjName(e.target.value)} />
              </label>
              <button className="primary" onClick={() => setStage('sources')}>
                Next ▶
              </button>
            </div>
            <p className="small muted">
              The AI proposes a first draft of the whole edit — which clips, in what order, where to trim.
              You review every stage and approve before the next one runs. The AI proposes; you decide.
            </p>
          </div>
        )}

        {stage === 'sources' && (
          <div className="panel">
            <h2>Pick footage &amp; music</h2>
            <p className="small muted">Originals are opened read-only and never leave this Mac (ADR-002).</p>
            <div className="row wrap">
              <label>
                Folder{' '}
                <select value={mediaRoot} onChange={(e) => setMediaRoot(e.target.value)}>
                  {FOLDERS.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="row wrap" style={{ marginTop: 8 }}>
              <label>
                Music{' '}
                <select value={track} onChange={(e) => setTrack(e.target.value)}>
                  {TRACKS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="gatebar row spread">
              <button onClick={() => setStage('create')}>◀ Back</button>
              <button className="primary" onClick={startAnalysis}>
                Import &amp; analyse ▶
              </button>
            </div>
          </div>
        )}

        {stageProps && stage === 'ingest' && <IngestStage {...stageProps} />}
        {stageProps && stage === 'curate' && <CurateStage {...stageProps} />}
        {stageProps && stage === 'trim' && <TrimStage {...stageProps} />}
        {stageProps && stage === 'finalize' && <FinalizeStage {...stageProps} />}
        {stageProps && stage === 'export' && <ExportStage {...stageProps} />}

        <Provenance data={data} />
      </div>
    </>
  )
}

function Provenance({ data }: { data: SeedData | null }) {
  if (!data) return null
  const p = data.project
  return (
    <details className="panel" style={{ marginTop: 16 }}>
      <summary className="small muted">
        Inspect project.json state — origin · disposition · approvals persist here (WO-103 will own this on disk)
      </summary>
      <div className="small" style={{ marginTop: 8 }}>
        <strong>stage_approvals</strong>
        <pre style={{ whiteSpace: 'pre-wrap', margin: '4px 0' }}>{JSON.stringify(p.stage_approvals, null, 1)}</pre>
        <div style={{ overflowX: 'auto' }}>
          <table className="src">
            <thead>
              <tr>
                <th>source</th>
                <th>incl</th>
                <th>order</th>
                <th>deleted</th>
                <th>origin.segments</th>
                <th>disposition</th>
              </tr>
            </thead>
            <tbody>
              {p.clips.map((c) => (
                <tr key={c.source_id}>
                  <td>{c.source_id}</td>
                  <td>{c.included ? 'Y' : 'n'}</td>
                  <td>{c.order}</td>
                  <td>{c.deleted ? 'Y' : 'n'}</td>
                  <td>{c.origin.segments}</td>
                  <td>{c.proposals.segments?.disposition ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </details>
  )
}
