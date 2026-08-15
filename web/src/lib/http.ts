export function isAbortError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === 'AbortError') return true
  if (typeof err === 'object' && err !== null && 'name' in err && (err as { name: string }).name === 'AbortError') {
    return true
  }
  return false
}

export function humanizeError(err: unknown): string {
  if (isAbortError(err)) return ''
  if (err instanceof TypeError) return 'Could not reach the SafetyView API. Check that it is running, then retry.'
  if (err instanceof Error && err.message) {
    if (/failed to fetch/i.test(err.message)) {
      return 'Could not reach the SafetyView API. Check that it is running, then retry.'
    }
    return err.message
  }
  return 'Something went wrong. Please retry.'
}

export async function fetchJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal })
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}
