// WO-109 · Manual curation — include/exclude, delete/restore, reorder. No assist
// proposes inclusion or order in M1 (§5.5). Order stays dense across non-deleted
// clips, so delete/restore renumber to keep the store invariant satisfied.
import type { Clip, Project } from '../types/contracts'
import { ClipThumb, baseName, fmtDur, orderedClips, sourceOf } from '../app/ui'

type Mutate = (fn: (p: Project) => void) => void

function renumber(p: Project): void {
  p.clips.filter((c) => !c.deleted).sort((a, b) => a.order - b.order).forEach((c, i) => { c.order = i + 1 })
}
function find(p: Project, id: string): Clip {
  return p.clips.find((c) => c.source_id === id)!
}

export function CurateView({ project, onMutate }: { project: Project; onMutate: Mutate }) {
  const clips = orderedClips(project)

  const setIncluded = (id: string, v: boolean) => onMutate((p) => { const c = find(p, id); c.included = v; c.origin.included = 'user' })
  const setDeleted = (id: string, v: boolean) => onMutate((p) => { find(p, id).deleted = v; renumber(p) })
  const move = (id: string, dir: -1 | 1) => onMutate((p) => {
    const live = p.clips.filter((c) => !c.deleted).sort((a, b) => a.order - b.order)
    const i = live.findIndex((c) => c.source_id === id)
    const j = i + dir
    if (j < 0 || j >= live.length) return
    const a = find(p, live[i].source_id), b = find(p, live[j].source_id)
    ;[a.order, b.order] = [b.order, a.order]
    a.origin.order = 'user'; b.origin.order = 'user'
  })

  return (
    <div className="clip-list">
      {clips.map((c) => {
        const s = sourceOf(project, c)!
        const cls = ['clip', c.deleted ? 'deleted' : '', !c.included ? 'excluded' : '', !s.readable ? 'unreadable' : ''].filter(Boolean).join(' ')
        return (
          <div key={c.source_id} className={cls}>
            <ClipThumb source={s} />
            <div className="clip-body">
              <div className="row spread">
                <strong>{baseName(s.path)} <span className="small muted">#{c.order}</span></strong>
                <span className="small muted">{fmtDur(s.duration_s)} · {s.orientation} · {s.codec}</span>
              </div>
              <div className="row wrap" style={{ marginTop: 6 }}>
                {c.deleted ? (
                  <button onClick={() => setDeleted(c.source_id, false)}>Restore</button>
                ) : (
                  <>
                    <button disabled={!s.readable} onClick={() => setIncluded(c.source_id, !c.included)}>{c.included ? 'Exclude' : 'Include'}</button>
                    <button onClick={() => move(c.source_id, -1)} title="Move earlier">↑</button>
                    <button onClick={() => move(c.source_id, 1)} title="Move later">↓</button>
                    <button className="danger" onClick={() => setDeleted(c.source_id, true)}>Delete</button>
                  </>
                )}
                {!s.readable && <span className="badge flag">unreadable — cannot include</span>}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
