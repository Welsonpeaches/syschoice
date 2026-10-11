/**
 * Node 26 ships a `localStorage` global that throws unless the process is
 * started with `--localstorage-file`, and it shadows the one jsdom provides.
 * Tests get a plain in-memory implementation instead.
 */
class MemoryStorage implements Storage {
  private map = new Map<string, string>()

  get length() {
    return this.map.size
  }

  clear() {
    this.map.clear()
  }

  getItem(key: string) {
    return this.map.has(key) ? (this.map.get(key) as string) : null
  }

  key(index: number) {
    return [...this.map.keys()][index] ?? null
  }

  removeItem(key: string) {
    this.map.delete(key)
  }

  setItem(key: string, value: string) {
    this.map.set(key, String(value))
  }
}

const storage = new MemoryStorage()

for (const target of [globalThis, typeof window !== 'undefined' ? window : undefined]) {
  if (!target) continue
  Object.defineProperty(target, 'localStorage', {
    value: storage,
    configurable: true,
    writable: true,
  })
}
