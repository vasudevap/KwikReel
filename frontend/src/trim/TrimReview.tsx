// WO-110 · Trim review — the AI's proposal per clip with its reason, and the
// override controls (adjust / remove). Accept happens at the trim gate (App).
// Every proposal shows its human_text; a proposal with no reason is a bug (ADR-006).
import { useRef, useState } from 'react'
import type { ReelClient } from '../app/client'
import type { Clip, Project } from '../types/contracts'
import { ClipThumb, DispositionBadge, OriginBadge, ReasonList, TrimBar, baseName, fmtDur, orderedClips, sourceOf } from '../app/ui'

type Mutate = (fn: (p: Project) => void) => void
const MIN = 1.0 // universal 1.0 s floor (G-9)

// One player, two starting points: "Play trim" jumps to [inS, outS) and stops
// once at the out point (then plays freely — it must not trap scrubbing past
// it); "Play original" plays the whole clip for comparison. Both call .play()
// directly from the click handler rather than relying on the `autoplay`
// attribute, which some browsers silently ignore on a just-mounted element.
function ClipPreview({ src, inS, outS }: { src: string; inS: number; outS: number }) {
  const ref = useRef<HTMLVideoElement>(null)
  const stopAt = useRef<number | null>(null)

  // Calling .play() in the same tick as setting currentTime races the seek
  // the browser just started — the seek can abort the play attempt (rejects
  // with AbortError), intermittently, since it depends on how long the seek
  // takes. So play() waits for the seek to actually finish ('seeked'). And
  // seeking before metadata has loaded (readyState 0, right after mount) can
  // wedge some browsers' fetch for the element indefinitely — so that waits
  // for 'loadedmetadata' first. Both are one-shot listeners keyed off real
  // media events, not fixed delays.
  const play = (from: number, stop: number | null) => {
    const v = ref.current
    if (!v) return
    stopAt.current = stop
    const start = () => { v.play().catch(() => {}) } // e.g. autoplay policy — native controls still work
    const seekThenStart = () => {
      if (v.currentTime === from) { start(); return }
      const onSeeked = () => { v.removeEventListener('seeked', onSeeked); start() }
      v.addEventListener('seeked', onSeeked)
      v.currentTime = from
    }
    if (v.readyState >= 1) {
      seekThenStart()
    } else {
      const onReady = () => { v.removeEventListener('loadedmetadata', onReady); seekThenStart() }
      v.addEventListener('loadedmetadata', onReady)
    }
  }

  return (
    <div style={{ marginTop: 6 }}>
      <div className="row wrap small" style={{ marginBottom: 4 }}>
        <button type="button" onClick={() => play(inS, outS)}>▶ Play trim</button>
        <button type="button" onClick={() => play(0, null)}>▶ Play original</button>
      </div>
      <video
        ref={ref}
        key={src}
        src={src}
        controls
        width={220}
        style={{ borderRadius: 6, background: '#000' }}
        onTimeUpdate={(e) => {
          if (stopAt.current != null && e.currentTarget.currentTime >= stopAt.current) {
            e.currentTarget.pause()
            stopAt.current = null // one-shot: don't re-trap manual scrubbing past it
          }
        }}
      />
    </div>
  )
}

export function TrimView({ project, onMutate, client }: { project: Project; onMutate: Mutate; client: ReelClient }) {
  const clips = orderedClips(project).filter((c) => c.included && !c.deleted)
  const find = (p: Project, id: string): Clip => p.clips.find((c) => c.source_id === id)!
  const [previewing, setPreviewing] = useState<string | null>(null)

  return (
    <div className="clip-list">
      {clips.map((c) => {
        const s = sourceOf(project, c)!
        const prop = c.proposals.segments
        const seg = c.segments[0]
        const open = previewing === c.source_id
        const proxy = client.proxyUrl(s.source_id)
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
                <button onClick={() => setPreviewing(open ? null : c.source_id)}>{open ? '■ Close preview' : '▶ Preview'}</button>
                <button className="danger" onClick={remove}>Remove suggestion</button>
              </div>
              {open && (proxy
                ? <ClipPreview src={proxy} inS={seg.in_s} outS={seg.out_s} />
                : <p className="small muted">Preview plays here in live mode.</p>)}
              {prop ? <ReasonList reasons={prop.reasons} /> : <p className="small muted">No proposal yet — run AI trim.</p>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
