import ReactDOM from 'react-dom/client'

// The v3z rack replaces the WO-107–110 frontend, which was deleted in the
// 2026-07-28 clean cut. Until `src/rack/` exists this is a placeholder that
// keeps the build green.
//
// ADR-011 wiring, preserved so it is not rediscovered: the server injects a
// per-launch capability token into the page as `__REEL_TOKEN__`. Its presence
// is what distinguishes a live backend from `vite dev` with no backend at all,
// and every state-changing request must carry it.
const live = typeof (globalThis as { __REEL_TOKEN__?: string }).__REEL_TOKEN__ === 'string'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <p style={{ font: '13px ui-monospace, monospace', padding: '2rem', color: '#888' }}>
    KwikReel — frontend not built yet ({live ? 'live backend detected' : 'no backend'}).
    The v3z rack is planned in <code>docs/implementation-plans/PLAN-v3z-rebuild.md</code>.
  </p>,
)
