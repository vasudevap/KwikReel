import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const frontendRoot = new URL('../../', import.meta.url)

test('the manifest correction changes no dependency or script contract', async () => {
  const manifest = JSON.parse(
    await readFile(new URL('package.json', frontendRoot), 'utf8'),
  )
  assert.deepEqual(manifest.scripts, {
    dev: 'vite',
    build: 'tsc && vite build',
    preview: 'vite preview',
    typecheck: 'tsc --noEmit',
  })
  assert.deepEqual(manifest.dependencies, {
    react: '^18.3.1',
    'react-dom': '^18.3.1',
  })
  assert.deepEqual(manifest.devDependencies, {
    '@types/react': '^18.3.3',
    '@types/react-dom': '^18.3.0',
    '@vitejs/plugin-react': '^4.3.1',
    typescript: '^5.5.3',
    vite: '^5.3.4',
  })
  assert.match(manifest.description, /ADP-003 is authorized/)
  assert.doesNotMatch(manifest.description, /waits on WO-124/)
})

test('the generated contract remains visibly generated and read-only', async () => {
  const generated = await readFile(
    new URL('src/types/contracts.ts', frontendRoot),
    'utf8',
  )
  assert.match(generated, /^\/\/ GENERATED FILE — DO NOT EDIT\./)
  assert.match(generated, /export interface Project/)
  assert.match(generated, /schema_version: 2/)
})

test('the app discovers every future lane through its frozen slot seam', async () => {
  const main = await readFile(new URL('src/main.tsx', frontendRoot), 'utf8')
  for (const lane of ['monitor', 'sound', 'index', 'editor', 'log', 'reel']) {
    assert.match(main, new RegExp(`'\\./${lane}/slot\\.ts'`))
  }
})

test('the empty shell consumes exactly the frozen 662px column height', async () => {
  const css = await readFile(new URL('src/app/app.css', frontendRoot), 'utf8')
  const expected = {
    reel: 84,
    transport: 95,
    sound: 105,
    editor: 130,
    index: 145,
    log: 88,
  }
  for (const [slot, height] of Object.entries(expected)) {
    assert.match(
      css,
      new RegExp(`\\.kr-app__slot--${slot}\\s*\\{[^}]*height:\\s*${height}px`, 's'),
    )
  }
  assert.equal(Object.values(expected).reduce((sum, value) => sum + value, 0) + 15, 662)
})
