// WO-108 · Timeline sequence view — ordered included clips with their trims, the
// running total vs target, the music track, and a proxy preview player.
import { useState } from 'react'
import type { Project } from '../types/contracts'
import type { ReelClient } from '../app/client'
import { ClipThumb, TrimBar, baseName, fmtDur, orderedClips, segDur, sourceOf, timelineTotal } from '../app/ui'

export function Timeline({ project, client }: { project: Project; client: ReelClient }) {
  const included = orderedClips(project).filter((c) => c.included && !c.deleted)
  const [selected, setSelected] = useState<string | null>(included[0]?.source_id ?? null)
  const total = timelineTotal(project)
  const over = total > project.target_duration_s
  const selClip = included.find((c) => c.source_id === selected) ?? included[0]
  const selSource = selClip && sourceOf(project, selClip)
  const proxy = selSource ? client.proxyUrl(selSource.source_id) : ''

  return (
    <div className="panel">
      <div className="row spread wrap">
        <strong>Timeline</strong>
        <span className="small muted">
          running total <strong className={over ? '' : ''} style={{ color: over ? 'var(--warn)' : 'inherit' }}>{fmtDur(total)}</strong> / target {fmtDur(project.target_duration_s)} · music: {baseName(project.music.track_ref) || '—'}
        </span>
      </div>
      {included.length === 0 && <p className="small muted">No clips included yet — include some in Curate.</p>}
      <div className="clip-list" style={{ marginTop: 8 }}>
        {included.map((c) => {
          const s = sourceOf(project, c)!
          const active = selClip?.source_id === c.source_id
          return (
            <div key={c.source_id} className="clip" onClick={() => setSelected(c.source_id)} style={{ cursor: 'pointer', outline: active ? '2px solid var(--accent)' : 'none' }}>
              <ClipThumb source={s} />
              <div className="clip-body">
                <div className="row spread"><strong>{baseName(s.path)} <span className="small muted">#{c.order}</span></strong><span className="small muted">{fmtDur(segDur(c.segments))} of {fmtDur(s.duration_s)}</span></div>
                <TrimBar durationS={s.duration_s} segments={c.segments} />
              </div>
            </div>
          )
        })}
      </div>
      {proxy ? (
        <video key={proxy} src={proxy} controls width={200} style={{ marginTop: 10, borderRadius: 6, background: '#000' }} />
      ) : (
        <p className="small muted" style={{ marginTop: 10 }}>Proxy preview plays here in live mode ({selSource ? baseName(selSource.path) : 'no clip'}).</p>
      )}
    </div>
  )
}
