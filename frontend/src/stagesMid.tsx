import { useEffect, useState } from 'react'
import type { StageProps } from './appTypes'
import type { SeedData } from './fixtures'
import { DEMO_SPEEDS, REAL_JOB_SECONDS, runJob } from './fakeAsync'
import { JobProgress, ClipThumb, StageBar, fmtDur, baseName } from './ui'
import {
  approveStage,
  clipRenderSeconds,
  liveClips,
  move,
  setDeleted,
  setIncluded,
  sourceOf,
  timelineSeconds,
} from './store'

function groupDups(data: SeedData): { group: string; ids: string[] }[] {
  const m = new Map<string, string[]>()
  for (const a of Object.values(data.analyses)) {
    if (a.dup_group) m.set(a.dup_group, [...(m.get(a.dup_group) || []), a.source_id])
  }
  return [...m.entries()].filter(([, ids]) => ids.length > 1).map(([group, ids]) => ({ group, ids }))
}

export function IngestStage({ data, update, speed, setSpeed, goto, projName }: StageProps) {
  const [done, setDone] = useState(false)
  const [prog, setProg] = useState(0)
  const [remain, setRemain] = useState(REAL_JOB_SECONDS)

  useEffect(() => {
    setDone(false)
    setProg(0)
    const opt = DEMO_SPEEDS.find((s) => s.id === speed) ?? DEMO_SPEEDS[1]
    const job = runJob(
      opt.wallSeconds,
      (p, r) => {
        setProg(p)
        setRemain(r)
      },
      () => setDone(true),
    )
    return () => job.cancel()
  }, [speed])

  const { project } = data
  const sources = project.sources
  const readable = sources.filter((s) => s.readable)
  const unreadable = sources.filter((s) => !s.readable)
  const dups = groupDups(data)
  const dupOf = (id: string) => dups.find((d) => d.ids.includes(id))?.group

  if (!done) {
    return (
      <div>
        <h1>Importing &amp; analysing “{projName}”</h1>
        <p className="muted small">
          Probing {sources.length} clips, building proxies, and measuring sharpness, shake, motion and
          audio per second. In production this is about 5 minutes for a 50-clip day — the screen below is
          built for that wait.
        </p>
        <JobProgress
          label="Analysing footage…"
          progress={prog}
          remainingRealS={remain}
          speed={speed}
          onSpeed={setSpeed}
        />
      </div>
    )
  }

  return (
    <div>
      <h1>Import review — “{projName}”</h1>
      <p className="muted small">
        {readable.length} readable clips · {unreadable.length} unreadable · {dups.length} near-duplicate
        group(s). Detection counts people later (M2) — never identity.
      </p>
      <StageBar
        left={<span className="small muted">Approving records a timestamp in project.json (survives reload).</span>}
        right={
          <button
            className="primary"
            onClick={() => {
              update((p) => approveStage(p, 'ingest'))
              goto('curate')
            }}
          >
            Approve import ▶ Curate
          </button>
        }
      />
      {unreadable.length > 0 && (
        <div className="err">
          ⚠ {unreadable.length} clip couldn’t be read ({unreadable.map((s) => baseName(s.path)).join(', ')}).
          It’s kept and surfaced here — never silently dropped — but it can’t be included in the reel.
        </div>
      )}
      <div className="panel" style={{ overflowX: 'auto' }}>
        <table className="src">
          <thead>
            <tr>
              <th></th>
              <th>Clip</th>
              <th>Captured</th>
              <th>Length</th>
              <th>Orient.</th>
              <th>Audio</th>
              <th>GPS</th>
              <th>Dup</th>
              <th>Readable</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.source_id}>
                <td>
                  <ClipThumb source={s} w={30} />
                </td>
                <td>
                  {baseName(s.path)}
                  <br />
                  <code className="path">{s.path}</code>
                </td>
                <td>{s.captured_at ? s.captured_at.slice(11, 16) : '—'}</td>
                <td>{s.readable ? fmtDur(s.duration_s) : '—'}</td>
                <td>{s.orientation}</td>
                <td>{s.has_audio ? 'yes' : 'silent'}</td>
                <td>{s.has_gps ? 'flag only' : 'no'}</td>
                <td>{dupOf(s.source_id) ? <span className="badge flag">{dupOf(s.source_id)}</span> : '—'}</td>
                <td>{s.readable ? 'yes' : <span className="badge dismissed">no</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function CurateStage({ data, update, goto }: StageProps) {
  const { project } = data
  const clips = liveClips(project)
  const deleted = project.clips.filter((c) => c.deleted)
  const total = timelineSeconds(project)
  const target = project.target_duration_s

  return (
    <div>
      <h1>Curate the day by hand</h1>
      <p className="muted small">
        You decide what’s in and what order — no AI proposes inclusion or order in M1 (ADR-009). The
        AI’s first suggestion comes at the next step (trim).
      </p>
      <StageBar
        left={
          <div className="small">
            Running total <strong>{fmtDur(total)}</strong> vs target <strong>{fmtDur(target)}</strong>{' '}
            <span className="muted">— reference only, nothing is enforced.</span>
          </div>
        }
        right={
          <button className="primary" onClick={() => goto('trim')}>
            Continue ▶ AI trim
          </button>
        }
      />

      <div className="clip-list" style={{ marginTop: 10 }}>
        {clips.map((c, i) => {
          const s = sourceOf(project, c.source_id)
          const canInclude = s.readable
          return (
            <div key={c.source_id} className={`clip ${!c.included ? 'excluded' : ''} ${!s.readable ? 'unreadable' : ''}`}>
              <ClipThumb source={s} />
              <div className="clip-body">
                <div className="row spread wrap">
                  <strong>
                    {i + 1}. {baseName(s.path)}
                  </strong>
                  <span className="small muted">
                    {s.readable ? fmtDur(clipRenderSeconds(c)) : 'unreadable'} · {s.orientation}
                    {!s.has_audio && s.readable ? ' · silent' : ''}
                  </span>
                </div>
                <div className="row wrap" style={{ marginTop: 6 }}>
                  <button disabled={!canInclude} onClick={() => update((p) => setIncluded(p, c.source_id, !c.included))}>
                    {c.included ? 'Exclude' : 'Include'}
                  </button>
                  <button onClick={() => update((p) => move(p, c.source_id, -1))} disabled={i === 0}>
                    ↑
                  </button>
                  <button onClick={() => update((p) => move(p, c.source_id, 1))} disabled={i === clips.length - 1}>
                    ↓
                  </button>
                  <button className="danger" onClick={() => update((p) => setDeleted(p, c.source_id, true))}>
                    Delete
                  </button>
                  {!c.included && canInclude && <span className="badge dismissed">excluded — won’t render</span>}
                  {!s.readable && <span className="badge flag">unreadable — can’t include</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {deleted.length > 0 && (
        <>
          <h2>Deleted ({deleted.length}) — retained for exact restore</h2>
          <div className="clip-list">
            {deleted.map((c) => {
              const s = sourceOf(project, c.source_id)
              return (
                <div key={c.source_id} className="clip deleted">
                  <ClipThumb source={s} w={40} />
                  <div className="clip-body row spread">
                    <span>{baseName(s.path)}</span>
                    <button onClick={() => update((p) => setDeleted(p, c.source_id, false))}>Restore</button>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
