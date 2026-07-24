import { useEffect, useState } from 'react'
import type { StageProps } from './appTypes'
import type { AudioMode } from './types'
import { DEMO_SPEEDS, REAL_JOB_SECONDS, runJob } from './fakeAsync'
import { approveStage, clipRenderSeconds, renderClips, sourceOf, timelineSeconds } from './store'
import { ClipThumb, DispositionBadge, JobProgress, TrimBar, baseName, fmtDur } from './ui'

export function FinalizeStage({ data, update, goto }: StageProps) {
  const { project } = data
  const clips = renderClips(project)
  const props = clips.map((c) => c.proposals.segments).filter(Boolean)
  const kept = props.filter((p) => p!.disposition === 'accepted' || p!.disposition === 'adjusted').length
  const dismissed = props.filter((p) => p!.disposition === 'dismissed').length

  return (
    <div>
      <h1>Finalize</h1>
      <p className="muted small">
        The reel below is exactly what will render. Editing anything after you approve here will visibly
        reset this approval.
      </p>

      <div className="panel">
        <div className="row spread wrap">
          <strong>
            {clips.length} clips · {fmtDur(timelineSeconds(project))}
          </strong>
          <span className="small muted">target {fmtDur(project.target_duration_s)} (reference)</span>
        </div>
        <p className="small muted" style={{ margin: '6px 0 0' }}>
          Trim proposals — kept (accepted/adjusted): <strong>{kept}</strong> · removed (dismissed):{' '}
          <strong>{dismissed}</strong>. This kept-vs-discarded snapshot is read from{' '}
          <code>disposition</code> (ADR-010) — the evidence that the assist earns its place.
        </p>
      </div>

      <div className="clip-list">
        {clips.map((c, i) => {
          const s = sourceOf(project, c.source_id)
          return (
            <div key={c.source_id} className="clip">
              <ClipThumb source={s} w={40} />
              <div className="clip-body">
                <div className="row spread wrap">
                  <span>
                    {i + 1}. {baseName(s.path)}{' '}
                    {!s.has_audio && <span className="badge flag">silent source</span>}
                  </span>
                  <span className="small muted">{fmtDur(clipRenderSeconds(c))}</span>
                </div>
                <div style={{ marginTop: 6 }}>
                  <TrimBar durationS={s.duration_s} segments={c.segments} />
                </div>
                {c.proposals.segments && (
                  <div style={{ marginTop: 4 }}>
                    <DispositionBadge d={c.proposals.segments.disposition} />
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="gatebar row spread wrap">
        <button onClick={() => goto('trim')}>◀ Back to trim</button>
        <button
          className="primary"
          onClick={() => {
            update((p) => approveStage(p, 'finalize'))
            goto('export')
          }}
        >
          Approve finalize ▶ Export
        </button>
      </div>
    </div>
  )
}

const ALL_MODES: { id: AudioMode; label: string; blurb: string }[] = [
  { id: 'music', label: 'Music', blurb: 'Your track only; clip audio is not mixed in.' },
  { id: 'clip', label: 'Natural clip audio', blurb: 'The clips’ own sound, in order. Silent clips get a matched silent pad.' },
  { id: 'silent', label: 'Silent', blurb: 'A valid silent audio track (no music, no clip sound).' },
]

export function ExportStage({ data, update, speed, setSpeed }: StageProps) {
  const { project } = data
  const [modes, setModes] = useState<AudioMode[]>(['music'])
  const [phase, setPhase] = useState<'choose' | 'render' | 'done'>('choose')
  const [prog, setProg] = useState(0)
  const [remain, setRemain] = useState(REAL_JOB_SECONDS)

  const clips = renderClips(project)
  const hasSilentSource = clips.some((c) => !sourceOf(project, c.source_id).has_audio)

  useEffect(() => {
    if (phase !== 'render') return
    setProg(0)
    const opt = DEMO_SPEEDS.find((s) => s.id === speed) ?? DEMO_SPEEDS[1]
    const job = runJob(
      opt.wallSeconds,
      (p, r) => {
        setProg(p)
        setRemain(r)
      },
      () => {
        update((p) => ({
          ...p,
          export: {
            audio_modes: modes,
            last_render: {
              path: `renders/${project.project_id}-${modes[0]}.mp4`,
              audio_mode: modes[0],
              rendered_at: new Date().toISOString(),
              qa: {
                passed: true,
                notes: ['1080×1920 H.264/AAC', 'not black', 'audio matches mode', 'duration within ±0.5s', 'safe-title margins ok'],
              },
            },
          },
        }))
        setPhase('done')
      },
    )
    return () => job.cancel()
  }, [phase, speed])

  function toggle(m: AudioMode) {
    setModes((cur) => (cur.includes(m) ? cur.filter((x) => x !== m) : [...cur, m]))
  }

  if (phase === 'render') {
    return (
      <div>
        <h1>Rendering {modes.length} version(s)…</h1>
        <p className="muted small">
          Encoding to 1080×1920 vertical. In production a 50-clip reel is about a 5-minute render — the
          screen is built for that wait.
        </p>
        <JobProgress label="Rendering reel…" progress={prog} remainingRealS={remain} speed={speed} onSpeed={setSpeed} />
      </div>
    )
  }

  if (phase === 'done') {
    const qa = project.export.last_render?.qa
    return (
      <div>
        <h1>Done ✓</h1>
        <div className="panel">
          <strong>Output QA passed</strong>
          <ul className="small">{qa?.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
        </div>
        <h2>Your reel — {modes.length} version(s)</h2>
        <div className="clip-list">
          {modes.map((m) => (
            <div key={m} className="clip">
              <div className="clip-body row spread wrap">
                <span>
                  <strong>{ALL_MODES.find((x) => x.id === m)?.label}</strong>{' '}
                  <code className="path">renders/{project.project_id}-{m}.mp4</code>
                </span>
                <button onClick={() => alert('Prototype: a real build would save the file here.')}>Save…</button>
              </div>
            </div>
          ))}
        </div>
        <div className="gatebar">
          <button onClick={() => setPhase('choose')}>◀ Export another version</button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>Export</h1>
      <p className="muted small">Pick one or more audio treatments. Each renders as its own file.</p>
      <div className="clip-list">
        {ALL_MODES.map((m) => (
          <label key={m.id} className="clip" style={{ cursor: 'pointer', alignItems: 'center' }}>
            <input type="checkbox" checked={modes.includes(m.id)} onChange={() => toggle(m.id)} />
            <div className="clip-body">
              <strong>{m.label}</strong>
              <div className="small muted">{m.blurb}</div>
              {m.id === 'clip' && hasSilentSource && (
                <div className="small" style={{ color: 'var(--warn)' }}>
                  Note: a silent source in this reel will get a matched silent pad to stay in sync.
                </div>
              )}
            </div>
          </label>
        ))}
      </div>
      <div className="gatebar row spread wrap">
        <span className="small muted">{modes.length} version(s) selected</span>
        <button className="primary" disabled={modes.length === 0} onClick={() => setPhase('render')}>
          Render {modes.length} version(s)
        </button>
      </div>
    </div>
  )
}
