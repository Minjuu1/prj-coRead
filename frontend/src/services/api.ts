import type { ChunkSource, DynamicAgent, LibraryPaper, Thread } from '../types'

const BASE = 'http://localhost:8000'

export async function uploadPaper(file: File, userId: string = 'anonymous'): Promise<{ paperId: string; status: string }> {
  const form = new FormData()
  form.append('file', file)
  form.append('userId', userId)
  const res = await fetch(`${BASE}/papers/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json()
}

export async function getUserPapers(userId: string): Promise<LibraryPaper[]> {
  const res = await fetch(`${BASE}/papers?userId=${encodeURIComponent(userId)}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.papers ?? []
}

export async function getPaperMeta(paperId: string): Promise<LibraryPaper | null> {
  const res = await fetch(`${BASE}/papers/${paperId}/meta`)
  if (!res.ok) return null
  return res.json()
}

export async function getPaperStatus(paperId: string): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/papers/${paperId}/status`)
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`)
  return res.json()
}

export async function reprocessPaper(paperId: string): Promise<void> {
  await fetch(`${BASE}/papers/${paperId}/reprocess`, { method: 'POST' })
}

export async function getAgents(paperId: string): Promise<DynamicAgent[]> {
  const res = await fetch(`${BASE}/papers/${paperId}/agents`)
  if (!res.ok) return []
  const data = await res.json()
  return data.agents ?? []
}

export async function getThreads(paperId: string): Promise<Thread[]> {
  const res = await fetch(`${BASE}/papers/${paperId}/threads`)
  if (!res.ok) return []
  const data = await res.json()
  return (data.threads ?? []).map((t: any) => ({
    ...t,
    createdAt: t.createdAt ? new Date(t.createdAt) : new Date(),
  }))
}

export interface StreamEvent {
  agent?: string
  token?: string
  done?: boolean
  sources?: ChunkSource[]
}

export async function* streamChat(
  threadId: string,
  content: string,
  history: { role: string; content: string }[],
  threadContext: string,
  paperId?: string | null,
  agentId?: string | null,
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE}/chat/${threadId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, userId: 'student', history, threadContext, paperId, agentId }),
  })

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6))
        } catch {
          // ignore parse errors
        }
      }
    }
  }
}
