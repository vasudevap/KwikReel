import ReactDOM from 'react-dom/client'
import { App } from './app/App'
import { createLiveClient } from './app/liveClient'
import { createMockClient } from './app/mockClient'
import './styles.css'

// Live when the server injected a capability token into the page (ADR-011);
// otherwise mock, so `vite dev` runs the whole flow with no backend (WO-107 gate).
const live = typeof (globalThis as { __REEL_TOKEN__?: string }).__REEL_TOKEN__ === 'string'
const client = live ? createLiveClient() : createMockClient()

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(<App client={client} />)
