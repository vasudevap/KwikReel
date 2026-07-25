// WO-107 · App shell — drives the M1 flow through a ReelClient (live or mock).
// The AI proposes each machine stage; the human approves before the next runs.
import { useState } from 'react'
import type { AudioMode, Project, ReelClient } from './client'
import { Progress, StageBar, Stepper, baseName, fmtDur, timelineTotal, type StepDef } from './ui'
import { Timeline } from '../timeline/Timeline'
import { CurateView } from '../edit/Curation'
import { TrimView } from '../trim/TrimReview'

type Stage = 'create' | 'sources' | 'import' | 'curate' | 'trim' | 'finalize' | 'export'
const STEPS: StepDef[] = [
  { id: 'create', label: 'Create' },
  { id: 'sources', label: 'Sources' },
  { id: 'import', label: 'Import', gate: true },
  { id: 'selection', label: 'AI select', inert: true },
  { id: 'curate', label: 'Curate' },
  { id: 'trim', label: 'AI trim', gate: true },
  { id: 'speed', label: 'Speed', inert: true },
  { id: 'finalize', label: 'Finalize', gate: true },
  { id: 'export', label: 'Export' },
]
const MODES: AudioMode[] = ['music', 'clip', 'silent']
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export function App({ client }: { client: ReelClient }) {
  const [project, setProject] = useState<Project | null>(null)
  const [stage, setStage] = useState<Stage>('create')
  const [busy, setBusy] = useState<{ label: string; progress: number } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('Beach Day')
  const [mediaRoot, setMediaRoot] = useState('')
  const [track, setTrack] = useState('')

  const currentIdx = STEPS.findIndex((s) => s.id === stage)
  const doneIds = new Set(STEPS.filter((s, i) => i < currentIdx && !s.inert).map((s) => s.id))

  async function guard(fn: () => Promise<void>) {
    try { await fn() } catch (e) { setError(e instanceof Error ? e.message : String(e)) }
  }

  async function runJob(label: string, start: () => Promise<string>) {
    setError(null); setBusy({ label, progress: 0 })
    try {
      const jobId = await start()
      for (;;) {
        const st = await client.jobStatus(jobId)
        setBusy({ label, progress: st.progress })
        if (st.state === 'done') return
        if (st.state === 'error') throw new Error(st.error || 'the job failed')
        await sleep(200)
      }
    } finally { setBusy(null) }
  }

  async function refresh(id: string) { setProject(await client.getProject(id)) }

  async function mutate(fn: (p: Project) => void) {
    if (!project) return
    const next: Project = JSON.parse(JSON.stringify(project))
    fn(next)
    await guard(async () => { setProject(await client.saveProject(next)) })
  }

  const createAndImport = () => guard(async () => {
    const p = await client.createProject({ media_root: mediaRoot, track_ref: track, target_duration_s: 75 })
    if (name.trim()) { p.name = name.trim(); setProject(await client.saveProject(p)) } else setProject(p)
    await runJob('Importing & building proxies… (a ~5-minute job)', () => client.scan(p.project_id))
    await refresh(p.project_id)
    setStage('import')
  })
  const browseFolder = () => guard(async () => {
    const path = await client.pickFolder()
    if (path) setMediaRoot(path)
  })
  const approveIngest = () => guard(async () => { setProject(await client.approve(project!.project_id, 'ingest')); setStage('curate') })
  const runTrim = () => guard(async () => {
    await runJob('Analysing clips…', () => client.analyze(project!.project_id))
    await runJob('Proposing trims…', () => client.propose(project!.project_id))
    await refresh(project!.project_id); setStage('trim')
  })
  const approveTrim = () => guard(async () => { setProject(await client.approve(project!.project_id, 'trim')); setStage('finalize') })
  const renderDraft = () => guard(async () => { await runJob('Rendering draft…', () => client.finalize(project!.project_id)); await refresh(project!.project_id) })
  const approveFinalize = () => guard(async () => { setProject(await client.approve(project!.project_id, 'finalize')); setStage('export') })
  const doExport = (mode: AudioMode) => guard(async () => { await runJob(`Exporting ${mode}…`, () => client.export(project!.project_id, mode)); await refresh(project!.project_id) })

  const trimApproved = !!project?.stage_approvals.finalize
  const unreadable = project?.sources.filter((s) => !s.readable) ?? []

  return (
    <>
      <div className="proto-banner">
        {client.mode === 'mock'
          ? <>Mock mode — <strong>fake data, no backend</strong>. Run the local server to switch to live (no code changes).</>
          : <>Live — connected to the local backend on 127.0.0.1. Originals are read-only and never leave this Mac (ADR-002).</>}
      </div>
      <div className="shell">
        <div className="row spread wrap">
          <h1 style={{ margin: 0 }}>🎬 KwikReel <span className="muted small">— first-draft editor</span></h1>
          {project && <button onClick={() => { setProject(null); setStage('create'); setError(null) }}>Start over</button>}
        </div>
        <Stepper steps={STEPS} currentIdx={currentIdx} doneIds={doneIds} />

        {error && <div className="err">⚠ {error}</div>}
        {busy && <Progress label={busy.label} progress={busy.progress} />}

        {stage === 'create' && (
          <div className="panel">
            <h2>New project</h2>
            <label>Name <input value={name} onChange={(e) => setName(e.target.value)} /></label>
            <p className="small muted">The AI proposes a first draft of the whole edit — which clips, where to trim — each with a reason. You review every stage and approve before the next runs. The AI proposes; you decide.</p>
            <StageBar right={<button className="primary" onClick={() => setStage('sources')}>Next ▶</button>} />
          </div>
        )}

        {stage === 'sources' && (
          <div className="panel">
            <h2>Pick footage &amp; music</h2>
            <p className="small muted">Point at a folder of clips and a local music track. {client.mode === 'live' ? 'Paths are on this Mac.' : 'In mock mode any values work.'}</p>
            <div><label>Folder <input style={{ width: 360 }} placeholder="/Users/you/Movies/Beach Day" value={mediaRoot} onChange={(e) => setMediaRoot(e.target.value)} /></label> <button type="button" onClick={browseFolder}>Browse…</button></div>
            <div style={{ marginTop: 8 }}><label>Music <input style={{ width: 360 }} placeholder="/Users/you/Music/track.m4a" value={track} onChange={(e) => setTrack(e.target.value)} /></label></div>
            <StageBar left={<button onClick={() => setStage('create')}>◀ Back</button>} right={<button className="primary" disabled={!mediaRoot} onClick={createAndImport}>Create &amp; import ▶</button>} />
          </div>
        )}

        {stage === 'import' && project && (
          <div className="panel">
            <h2>Import review — {project.name}</h2>
            <p className="small muted">{project.sources.length} sources probed. Unreadable files are surfaced, never dropped.</p>
            {unreadable.length > 0 && <div className="notice">{unreadable.length} unreadable source(s) will be excluded: {unreadable.map((s) => baseName(s.path)).join(', ')}</div>}
            <div style={{ overflowX: 'auto', marginTop: 8 }}>
              <table className="src"><thead><tr><th>source</th><th>readable</th><th>orient</th><th>codec</th><th>dur</th><th>audio</th></tr></thead>
                <tbody>{project.sources.map((s) => (
                  <tr key={s.source_id}><td>{baseName(s.path)}</td><td>{s.readable ? 'yes' : 'NO'}</td><td>{s.orientation}</td><td>{s.codec}</td><td>{fmtDur(s.duration_s)}</td><td>{s.has_audio ? 'yes' : 'no'}</td></tr>
                ))}</tbody></table>
            </div>
            <StageBar right={<button className="primary" onClick={approveIngest}>Approve import ▶</button>} />
          </div>
        )}

        {stage === 'curate' && project && (
          <div className="panel">
            <h2>Curate the day</h2>
            <p className="small muted">Include the keepers, drop the rest, reorder by hand. No assist chooses for you in M1. Running total {fmtDur(timelineTotal(project))} / target {fmtDur(project.target_duration_s)}.</p>
            <CurateView project={project} onMutate={mutate} />
            <StageBar left={<span className="small muted">manual curation — no gate</span>} right={<button className="primary" onClick={runTrim}>Run AI trim ▶</button>} />
          </div>
        )}

        {stage === 'trim' && project && (
          <div className="panel">
            <h2>Review the AI trims</h2>
            <p className="small muted">Each clip has a proposed in/out with a reason. Preview the trim, adjust or remove it, then approve. Reviewing is the product.</p>
            <TrimView project={project} onMutate={mutate} client={client} />
            <StageBar left={<button onClick={() => setStage('curate')}>◀ Curate</button>} right={<button className="primary" onClick={approveTrim}>Approve trims ▶</button>} />
          </div>
        )}

        {stage === 'finalize' && project && (
          <div className="panel">
            <h2>Finalize</h2>
            <Timeline project={project} client={client} />
            {client.mode === 'live' ? (
              <video key={client.draftUrl(project.project_id)} src={client.draftUrl(project.project_id)} controls width={220} style={{ marginTop: 10, borderRadius: 6, background: '#000' }} />
            ) : (
              <p className="small muted">Draft preview plays here in live mode.</p>
            )}
            <StageBar left={<button onClick={renderDraft}>Render draft</button>} right={<button className="primary" onClick={approveFinalize}>Approve &amp; go to export ▶</button>} />
          </div>
        )}

        {stage === 'export' && project && (
          <div className="panel">
            <h2>Export</h2>
            <p className="small muted">Export one file per audio mode. QA must pass before a file is offered.</p>
            <div className="clip-list">
              {MODES.map((m) => {
                const rec = project.export.last_render[m]
                return (
                  <div className="clip" key={m}>
                    <div className="clip-body row spread wrap">
                      <div><strong>{m}</strong> <span className="small muted">{m === 'music' ? 'your track' : m === 'clip' ? 'natural clip audio' : 'silent + valid track'}</span></div>
                      <div className="row wrap">
                        <button onClick={() => doExport(m)}>{rec ? 'Re-export' : 'Export'}</button>
                        {rec && client.mode === 'live' && <a href={client.downloadUrl(project.project_id, m)}><button className="primary">Download</button></a>}
                        {rec && client.mode === 'mock' && <span className="badge accepted">rendered</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            <StageBar left={<span className="small muted">{trimApproved ? 'finalize approved' : ''}</span>} />
          </div>
        )}
      </div>
    </>
  )
}
