import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Localhost-only, mirroring ADR-011's posture even for the prototype dev server.
export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5178 },
})
