// WO-110 · Trim review — the AI's proposal per clip with its reason, and the
// override controls (adjust / remove). Accept happens at the trim gate (App).
// Every proposal shows its human_text; a proposal with no reason is a bug (ADR-006).
import type { Clip, Project } from '../types/contracts'
import { ClipThumb, DispositionBadge, OriginBadge, ReasonList, TrimBar, baseName, fmtDur, orderedClips, sourceOf } from '../app/ui'

type Mutate = (fn: (p: Project) => void) => void
const MIN = 1.0 // universal 1.0 s floor (G-9)

export function TrimView({ project, onMutate }: { project: Project; onMutate: Mutate }) {
  const clips = orderedClips(project).filter((c) => c.included && !c.deleted)
  const find = (p: Project, id: string): Clip => p.clips.find((c) => c.source_id === id)!

  return (
    <div className="clip-list">
      {clips.map((c) => {
        const s = sourceOf(project, c)!
        const prop = c.proposals.segments
        const seg = c.segments[0]
        const markAdjusted = (x: Clip) => { x.origin.segments = 'user'; if (x.proposals.segments) x.proposals.segments.disposition = 'adjusted' }
        const setIn = (v: number) => onMutate((p) => { const x = find(p, c.source_id); const g = x.segments[0]; g.in_s = Math.min(Math.max(0, v), g.out_s - MIN); markAdjusted(x) })
        const setOut = (v: number) => onMutate((p) => { const x = find(p, c.source_id); const g = x.segments[0]; g.out_s = Math.max(Math.min(s.duration_s, v), g.in_s + MIN); markAdjusted(x) })
        const remove = () => onMutate((p) => { const x = find(p, c.source_id); x.segments = [{ in_s: 0, out_s: s.duration_s, speed: [] }]; x.origin.segments = 'user'; if (x.proposals.segments) x.proposals.segments.disposition = 'dismissed' })

        return (
          <div className="clip" key={c.source_id}>
            <ClipThumb source={s} />
            <div className="clip-body">
              <div className="row spread">
                <strong>{baseName(s.path)}</strong>
                <span>{prop && <DispositionBadge d={prop.disposition} />} <OriginBadge o={c.origin.segments} /></span>
              </div>
              <TrimBar durationS={s.duration_s} segments={c.segments} proposal={prop?.value} />
              <div className="row wrap small" style={{ marginTop: 6 }}>
                <label>in <input type="number" step="0.1" min={0} value={seg.in_s} onChange={(e) => setIn(parseFloat(e.target.value) || 0)} style={{ width: 66 }} /></label>
                <label>out <input type="number" step="0.1" value={seg.out_s} onChange={(e) => setOut(parseFloat(e.target.value) || 0)} style={{ width: 66 }} /></label>
                <span className="muted">kept {fmtDur(seg.out_s - seg.in_s)}</span>
                <button className="danger" onClick={remove}>Remove suggestion</button>
              </div>
              {prop ? <ReasonList reasons={prop.reasons} /> : <p className="small muted">No proposal yet — run AI trim.</p>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
