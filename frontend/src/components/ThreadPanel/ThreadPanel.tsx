import { useRef, useEffect, useState } from 'react'
import { useThreadStore } from '../../stores/threadStore'
import { usePaperStore } from '../../stores/paperStore'
import { MessageBubble } from './MessageBubble'
import { streamChat, getAgents } from '../../services/api'
import type { Message, Thread } from '../../types'

type AgentMode = 'auto' | string


// ─────────────────────────────────────
// Thread list item
// ─────────────────────────────────────
function ThreadItem({
  thread,
  active,
  onClick,
}: {
  thread: Thread
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        width: '100%',
        textAlign: 'left',
        padding: '10px 16px',
        background: active ? 'var(--bg-panel)' : 'transparent',
        borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
        border: 'none',
        borderBottom: '1px solid var(--border)',
        cursor: 'pointer',
        transition: 'background 0.1s',
      }}
    >
      <div
        style={{
          fontSize: '12px',
          fontWeight: active ? 600 : 400,
          color: active ? 'var(--text)' : 'var(--text-muted)',
          lineHeight: 1.4,
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}
      >
        {thread.contestablePoint}
      </div>
      <div
        style={{
          fontSize: '11px',
          color: 'var(--text-faint)',
          fontFamily: 'var(--font-mono)',
          marginTop: '2px',
        }}
      >
        {thread.status === 'open' ? 'open' : 'locked'}
      </div>
    </button>
  )
}

// ─────────────────────────────────────
// Chat view for active thread
// ─────────────────────────────────────
function ThreadChat({ thread }: { thread: Thread }) {
  const { messagesByThreadId, isStreaming, addMessage, setStreaming } = useThreadStore()
  const { paperId, agents, setActiveSources } = usePaperStore()
  const messages = messagesByThreadId[thread.id] ?? []

  const [input, setInput] = useState('')
  const [agentMode, setAgentMode] = useState<AgentMode>(
    (thread.suggestedAgent as AgentMode | undefined) ?? 'auto'
  )
  const [streamingText, setStreamingText] = useState('')
  const [streamingAgent, setStreamingAgent] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  // 스레드 전환 시 상태 초기화
  useEffect(() => {
    setStreamingText('')
    setStreamingAgent(null)
    setInput('')
    setAgentMode((thread.suggestedAgent as AgentMode | undefined) ?? 'auto')
  }, [thread.id])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      author: 'student',
      content: input.trim(),
      timestamp: new Date(),
    }
    addMessage(thread.id, userMsg)
    setInput('')
    setStreaming(true)
    setStreamingText('')
    setStreamingAgent(null)

    const seedHistory = (thread.seedMessages ?? []).map((sm) => ({
      role: 'assistant' as const,
      content: `[${sm.author}] ${sm.content}`,
    }))
    const history = [
      ...seedHistory,
      ...messages.map((m) => ({
        role: m.author === 'student' ? ('user' as const) : ('assistant' as const),
        content: m.content,
      })),
    ]

    let fullText = ''
    let agent: string = ''

    try {
      for await (const event of streamChat(
        thread.id,
        userMsg.content,
        history,
        `${thread.contestablePoint}\n${thread.openQuestion}`,
        paperId,
        agentMode === 'auto' ? null : agentMode,
      )) {
        if (event.agent) {
          agent = event.agent
          setStreamingAgent(agent)
        }
        if (event.token) {
          fullText += event.token
          setStreamingText(fullText)
        }
        if (event.done) {
          addMessage(thread.id, {
            id: crypto.randomUUID(),
            author: agent,
            content: fullText,
            timestamp: new Date(),
          })
          if (event.sources && event.sources.length > 0) {
            setActiveSources(event.sources)
          }
          setStreamingText('')
          setStreamingAgent(null)
        }
      }
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      {/* Thread header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        {thread.chunkSection && (
          <div style={{ fontSize: '10px', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)', letterSpacing: '0.06em', marginBottom: '6px' }}>
            {thread.chunkSection.toUpperCase()}
          </div>
        )}
        <div style={{ fontSize: '11px', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
          CONTESTABLE POINT
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.5, fontStyle: 'italic' }}>
          "{thread.contestablePoint}"
        </div>
        {thread.chunkContent && (
          <div style={{
            marginTop: '8px',
            padding: '8px 12px',
            background: 'var(--bg-panel)',
            borderRadius: 'var(--radius)',
            fontSize: '11px',
            color: 'var(--text-faint)',
            lineHeight: 1.5,
            borderLeft: '2px solid var(--border)',
          }}>
            {thread.chunkContent}…
          </div>
        )}
        <div
          style={{
            marginTop: '10px',
            padding: '8px 12px',
            background: 'var(--bg-panel)',
            borderRadius: 'var(--radius)',
            fontSize: '12px',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
          }}
        >
          {thread.openQuestion}
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {/* Seed messages (pre-generated agent conversation) */}
        {thread.seedMessages && thread.seedMessages.length > 0 && (
          <>
            {thread.seedMessages.map((sm, i) => (
              <MessageBubble
                key={`seed-${i}`}
                msg={{ id: `seed-${i}`, author: sm.author, content: sm.content, timestamp: new Date(0) }}
              />
            ))}
            <div style={{
              margin: '12px 0 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'var(--text-faint)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
            }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
              Join the discussion
              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
            </div>
          </>
        )}
        {messages.length === 0 && !isStreaming && !thread.seedMessages?.length && (
          <div style={{ color: 'var(--text-faint)', fontSize: '13px', textAlign: 'center', marginTop: '32px' }}>
            Share a question or thought.
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {streamingText && streamingAgent && (
          <MessageBubble
            msg={{ id: 'streaming', author: streamingAgent, content: streamingText, timestamp: new Date() }}
          />
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div style={{ borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        {/* To: 에이전트 선택 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px 0' }}>
          <span style={{
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-faint)',
            letterSpacing: '0.04em',
            flexShrink: 0,
          }}>
            To
          </span>
          {/* Auto button */}
          {[{ id: 'auto', tag: 'auto', color: null as string | null, colorIdx: -1 },
            ...agents.map(a => ({ id: a.id, tag: `@${a.id}`, color: `var(--agent-${a.color_index})`, colorIdx: a.color_index }))
          ].map((m) => {
            const active = agentMode === m.id
            const color = m.color ?? 'var(--accent)'
            return (
              <button
                key={m.id}
                onClick={() => setAgentMode(m.id)}
                style={{
                  padding: '2px 9px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: active ? 600 : 400,
                  border: `1px solid ${active ? color : 'var(--border)'}`,
                  borderRadius: '10px',
                  background: active ? (m.colorIdx >= 0 ? `var(--agent-${m.colorIdx}-bg)` : 'var(--accent-light)') : 'transparent',
                  color: active ? color : 'var(--text-faint)',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  whiteSpace: 'nowrap',
                }}
              >
                {m.tag}
              </button>
            )
          })}
        </div>
        <div style={{ padding: '8px 16px 14px', display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="Type a message (Enter to send)"
            disabled={isStreaming}
            rows={2}
            style={{
              flex: 1,
              resize: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              padding: '8px 12px',
              fontSize: '13px',
              lineHeight: 1.5,
              background: 'var(--bg)',
              color: 'var(--text)',
              outline: 'none',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border)')}
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            style={{
              padding: '8px 16px',
              background: isStreaming || !input.trim() ? 'var(--bg-panel)' : 'var(--accent)',
              color: isStreaming || !input.trim() ? 'var(--text-faint)' : 'var(--accent-fg)',
              border: 'none',
              borderRadius: 'var(--radius)',
              fontSize: '13px',
              fontWeight: 500,
              cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {isStreaming ? '···' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────
// Main panel
// ─────────────────────────────────────
export function ThreadPanel() {
  const { activeThreadId, setActiveThread, threads } = useThreadStore()
  const { paperId, setAgents } = usePaperStore()
  const [listOpen, setListOpen] = useState(false)

  // Load dynamic agents for this paper
  useEffect(() => {
    if (!paperId) return
    getAgents(paperId).then((agents) => {
      if (agents.length > 0) setAgents(agents)
    })
  }, [paperId])

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? null

  const handleSelectThread = (t: Thread) => {
    const nextId = t.id === activeThreadId ? null : t.id
    setActiveThread(nextId)
    if (nextId) {
      window.dispatchEvent(new CustomEvent('coread:scrollToThread', { detail: { threadId: nextId } }))
    }
    setListOpen(false)
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderLeft: '1px solid var(--border)',
        background: 'var(--bg)',
      }}
    >
      {/* 헤더 — 현재 스레드 제목 + 목록 버튼 */}
      <div style={{ flexShrink: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)', letterSpacing: '0.06em', overflow: 'hidden' }}>
            {activeThread
              ? <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontSize: '12px', fontWeight: 500 }}>{activeThread.contestablePoint}</span>
              : 'THREAD'}
          </div>
          <button
            onClick={() => setListOpen((v) => !v)}
            title="Thread list"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: '3px',
              padding: '4px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              borderRadius: '4px',
              flexShrink: 0,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-panel)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            {[0, 1, 2].map((i) => (
              <span key={i} style={{ display: 'block', width: '14px', height: '1.5px', background: 'var(--text-muted)', borderRadius: '1px' }} />
            ))}
          </button>
        </div>
      </div>

      {/* Overlay */}
      <div
        onClick={() => setListOpen(false)}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          zIndex: 200,
          opacity: listOpen ? 1 : 0,
          pointerEvents: listOpen ? 'auto' : 'none',
          transition: 'opacity 0.2s ease',
        }}
      />

      {/* Drawer — 오른쪽에서 슬라이드인 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '300px',
          background: 'var(--bg)',
          zIndex: 201,
          borderLeft: '1px solid var(--border)',
          boxShadow: '-8px 0 32px rgba(0,0,0,0.12)',
          transform: listOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Drawer 헤더 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 16px',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)', letterSpacing: '0.08em' }}>
            THREADS · {threads.length}
          </span>
          <button
            onClick={() => setListOpen(false)}
            style={{
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              color: 'var(--text-faint)',
              fontSize: '16px',
              lineHeight: 1,
              padding: '2px 6px',
              borderRadius: '4px',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-panel)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            ✕
          </button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {threads.map((t: Thread) => (
            <ThreadItem
              key={t.id}
              thread={t}
              active={t.id === activeThreadId}
              onClick={() => handleSelectThread(t)}
            />
          ))}
        </div>
      </div>

      {/* Chat view */}
      {activeThread ? (
        <ThreadChat thread={activeThread} />
      ) : (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            color: 'var(--text-faint)',
            fontSize: '13px',
          }}
        >
          <div>Select a thread</div>
          <button
            onClick={() => setListOpen(true)}
            style={{
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-faint)',
              background: 'var(--bg-panel)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '6px 12px',
              cursor: 'pointer',
            }}
          >
            Browse threads
          </button>
        </div>
      )}
    </div>
  )
}
