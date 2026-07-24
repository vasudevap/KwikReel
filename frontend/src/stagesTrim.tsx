import { useState } from 'react'
import type { StageProps } from './appTypes'
import type { Segment } from './types'
import {
  adjustTrim,
  applyProposal,
  approveStage,
  clipRenderSeconds,
  removeTrim,
  renderClips,
  rerunTrim,
  sourceOf,
} from './store'
import { ClipThumb, DispositionBadge, OriginBadge, ReasonList, TrimBar, baseName, fmtDur } from './ui'

const STEP = 0.5
const MIN_WINDOW = 1.0

export function TrimStage({ data, update, goto }: StageProps) {
  const { project, latent } = data
  const clips = renderClips(project)
  const [running, setRunning] = useState<Set<string>>(new Set())
  const [adjusting, setAdjusting] = useState<string | null>(null)

  const withProposal = clips.filter((c) => c.proposals.segments)
  const pendingCount = withProposal.filter((c) => c.proposals.segments!.disposition === 'pending').length
  const unproposed = clips.filter((c) => !c.proposals.segments && latent[c.source_id])

  function runTrim(id: string, rerun = false) {
    const lp = latent[id]
    if (!lp) return
    setRunning((r) => new Set(r).add(id))
    // Per-clip trim is fast (deterministic rules); a short delay just feels honest.
    setTimeout(() => {
      update((p) => (rerun ? rerunTrim(p, id, lp) : applyProposal(p, id, lp)))
      setRunning((r) => {
        const n = new Set(r)
        n.delete(id)
        return n
      })
    }, 450)
  }
  function trimAll() {
    unproposed.forEach((c, i) => setTimeout(() => runTrim(c.source_id), i * 200))
  }
  function adjust(id: string, seg: Segment, dIn: number, dOut: number, durationS: number) {
    let in_s = Math.max(0, Math.min(seg.in_s + dIn, durationS - MIN_WINDOW))
    let out_s = Math.min(durationS, Math.max(seg.out_s + dOut, in_s + MIN_WINDOW))
    in_s = Number(in_s.toFixed(1))
    out_s = Number(out_s.toFixed(1))
    update((p) => adjustTrim(p, id, [{ in_s, out_s, speed: [] }]))
  }

  return (
    <div>
      <h1>AI trim — you review every cut</h1>
      <p className="muted small">
        The AI proposes where to trim each clip and <em>why</em>. Some proposals are wrong on purpose —
        reviewing and fixing them is the whole point. Adjust, remove, or re-run anything.
      </p>

      <div className="row spread wrap">
        <div className="row wrap small">
          <button className="primary" onClick={trimAll} disabled={unproposed.length === 0}>
            AI Trim all ({unproposed.length})
          </button>
          <span className="muted">
            {withProposal.length}/{clips.length} proposed · {pendingCount} awaiting your review
          </span>
        </div>
      </div>

      <div className="clip-list" style={{ marginTop: 10 }}>
        {clips.map((c) => {
          const s = sourceOf(project, c.source_id)
          const seg = c.segments[0]
          const prop = c.proposals.segments
          const isRunning = running.has(c.source_id)
          return (
            <div key={c.source_id} className="clip">
              <ClipThumb source={s} />
              <div className="clip-body">
                <div className="row spread wrap">
                  <strong>{baseName(s.path)}</strong>
                  <span className="small muted">
                    keeps {fmtDur(clipRenderSeconds(c))} of {fmtDur(s.duration_s)}
                  </span>
                </div>

                <div style={{ margin: '8px 0' }}>
                  <TrimBar durationS={s.duration_s} segments={c.segments} proposal={prop && c.origin.segments === 'user' ? prop.value : undefined} />
                  <div className="small muted" style={{ marginTop: 2 }}>
                    keeping {seg.in_s}s–{seg.out_s}s
                    {prop && c.origin.segments === 'user' ? ' · dashed = original AI proposal' : ''}
                  </div>
                </div>

                {!prop && (
                  <div className="row wrap">
                    <button onClick={() => runTrim(c.source_id)} disabled={isRunning}>
                      {isRunning ? 'Analysing…' : 'AI trim this clip'}
                    </button>
                    {!latent[c.source_id] && <span className="small muted">no proposal available</span>}
                  </div>
                )}

                {prop && (
                  <>
                    <div className="row wrap" style={{ gap: 6, marginBottom: 4 }}>
                      <OriginBadge o={c.origin.segments} />
                      <DispositionBadge d={prop.disposition} />
                    </div>
                    <ReasonList reasons={prop.reasons} />

                    {adjusting === c.source_id ? (
                      <div className="row wrap" style={{ marginTop: 6, gap: 6 }}>
                        <span className="small muted">in</span>
                        <button onClick={() => adjust(c.source_id, seg, -STEP, 0, s.duration_s)}>−</button>
                        <button onClick={() => adjust(c.source_id, seg, +STEP, 0, s.duration_s)}>+</button>
                        <span className="small muted">out</span>
                        <button onClick={() => adjust(c.source_id, seg, 0, -STEP, s.duration_s)}>−</button>
                        <button onClick={() => adjust(c.source_id, seg, 0, +STEP, s.duration_s)}>+</button>
                        <button className="primary" onClick={() => setAdjusting(null)}>
                          Done
                        </button>
                      </div>
                    ) : (
                      <div className="row wrap" style={{ marginTop: 6, gap: 6 }}>
                        <button onClick={() => setAdjusting(c.source_id)}>Adjust</button>
                        <button className="danger" onClick={() => update((p) => removeTrim(p, c.source_id))}>
                          Remove suggestion
                        </button>
                        <button onClick={() => runTrim(c.source_id, true)} disabled={isRunning}>
                          {isRunning ? 'Re-running…' : 'Re-run'}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="gatebar row spread wrap">
        <span className="small muted">
          Approving trim promotes every untouched proposal to <strong>accepted</strong> and records the
          timestamp. {pendingCount > 0 ? `${pendingCount} still pending.` : 'Nothing pending.'}
        </span>
        <button
          className="primary"
          onClick={() => {
            update((p) => approveStage(p, 'trim'))
            goto('finalize')
          }}
        >
          Approve trim ▶ Finalize
        </button>
      </div>
    </div>
  )
}
