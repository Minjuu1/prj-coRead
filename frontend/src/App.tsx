import { useState, useCallback, useEffect, useRef } from 'react';
import {
  TextViewer,
  DiscussionList,
  DiscussionDetail,
  DocumentUpload,
} from './components';
import { useStore } from './store/useStore';
import { threadApi } from './services/api';
import { mockDocument, mockThreads } from './data/mockData';
import type { Thread, Document, Section, Message } from './types';
import type { AgentId } from './constants/agents';
import type { ThreadListItem } from './services/api';

// Temporary user ID for development (later: implement login flow)
const DEV_USER_ID = 'dev_user_001';

// Check for dev mode via URL param: ?dev (evaluated once at load)
const DEV_MODE = new URLSearchParams(window.location.search).has('dev');

function App() {
  const {
    document,
    setDocument,
    setSections,
    setThreads,
    setSelectedThreadId,
    fullThreads,
    setFullThreads,
    addFullThread,
  } = useStore();

  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [isLoadingThread, setIsLoadingThread] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const isResizing = useRef(false);

  // Dev mode: load mock data on mount
  useEffect(() => {
    if (DEV_MODE && !document) {
      console.log('[Dev Mode] Loading mock data...');
      setDocument(mockDocument as Document);
      setSections(mockDocument.parsedContent.sections);

      const threadListItems: ThreadListItem[] = mockThreads.map((t) => ({
        threadId: t.threadId,
        threadType: t.threadType,
        discussionType: t.discussionType,
        tensionPoint: t.tensionPoint,
        participants: t.participants,
        messageCount: t.messages?.length || 0,
        anchor: t.anchor,
      }));
      setThreads(threadListItems);
      setFullThreads(mockThreads);
    }
  }, [document, setDocument, setSections, setThreads, setFullThreads]);

  // Handle document upload complete
  const handleUploadComplete = useCallback(
    (uploadedDocument: Document, threads: unknown[]) => {
      console.log('[App] Upload complete, document:', uploadedDocument.documentId);
      console.log('[App] Threads received:', threads.length);

      // Store document
      setDocument(uploadedDocument);

      // Store sections
      const sections = uploadedDocument.parsedContent?.sections || [];
      setSections(sections as Section[]);

      // Store threads (convert to ThreadListItem format for list view)
      const threadListItems: ThreadListItem[] = (threads as Thread[]).map((t) => ({
        threadId: t.threadId,
        threadType: t.threadType,
        discussionType: t.discussionType,
        tensionPoint: t.tensionPoint,
        participants: t.participants,
        messageCount: t.messages?.length || 0,
        anchor: t.anchor,
      }));
      setThreads(threadListItems);

      // Also store full thread data for detail view
      setFullThreads(threads as Thread[]);
    },
    [setDocument, setSections, setThreads, setFullThreads]
  );

  // Handle thread selection
  const handleThreadSelect = async (threadId: string) => {
    console.log('[App] handleThreadSelect called, threadId:', threadId);
    console.log('[App] fullThreads length:', fullThreads.length);
    console.log('[App] fullThreads threadIds:', fullThreads.map((t) => t.threadId));
    setSelectedThreadId(threadId);

    // First, try to find in store
    const localThread = fullThreads.find((t) => t.threadId === threadId);
    console.log('[App] localThread found:', !!localThread);
    if (localThread) {
      setSelectedThread(localThread);
      return;
    }

    // If store is empty but we're in dev mode with mock data, use mock data directly
    if (DEV_MODE && fullThreads.length === 0) {
      console.log('[App] Dev mode: refreshing from mockThreads');
      setFullThreads(mockThreads);
      const mockThread = mockThreads.find((t) => t.threadId === threadId);
      if (mockThread) {
        setSelectedThread(mockThread);
        return;
      }
    }

    // If not found locally, fetch from API
    try {
      setIsLoadingThread(true);
      const thread = await threadApi.get(threadId);
      setSelectedThread(thread);
      // Add to store
      addFullThread(thread);
    } catch (err) {
      console.error('[App] Failed to fetch thread:', err);
      // Show error state instead of null
      setSelectedThread(null);
    } finally {
      setIsLoadingThread(false);
    }
  };

  const handleBack = () => {
    setSelectedThreadId(null);
    setSelectedThread(null);
  };

  const handleSendMessage = async (content: string, taggedAgent?: AgentId) => {
    if (!selectedThread) return;

    try {
      // Send message to API
      const response = await threadApi.sendMessage(
        selectedThread.threadId,
        content,
        taggedAgent
      );

      // Update local thread with new message(s)
      // The API might return the user message + agent response
      const newMessages: Message[] = Array.isArray(response) ? response : [response];

      const updatedThread = {
        ...selectedThread,
        messages: [...selectedThread.messages, ...newMessages],
      };

      setSelectedThread(updatedThread);

      // Update store
      const updatedFullThreads = fullThreads.map((t) =>
        t.threadId === selectedThread.threadId ? updatedThread : t
      );
      setFullThreads(updatedFullThreads);
    } catch (err) {
      console.error('[App] Failed to send message:', err);
      // Fallback: add message locally only
      const newMessage: Message = {
        messageId: `msg_${Date.now()}`,
        threadId: selectedThread.threadId,
        author: 'user' as const,
        content,
        references: [],
        taggedAgent,
        timestamp: new Date().toISOString(),
      };

      setSelectedThread({
        ...selectedThread,
        messages: [...selectedThread.messages, newMessage],
      });
    }
  };

  // If no document and not in dev mode, show upload screen
  // Dev mode will load mock data via useEffect
  if (!document && !DEV_MODE) {
    return <DocumentUpload userId={DEV_USER_ID} onComplete={handleUploadComplete} />;
  }

  // Still loading in dev mode
  if (!document) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  const handleThreadSelectFromSidebar = (threadId: string) => {
    handleThreadSelect(threadId);
    setIsSidebarOpen(false);
  };

  const handleMouseDown = () => {
    isResizing.current = true;
    window.document.body.style.cursor = 'col-resize';
    window.document.body.style.userSelect = 'none';
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftPanelWidth(Math.min(70, Math.max(30, newWidth)));
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      window.document.body.style.cursor = '';
      window.document.body.style.userSelect = '';
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // Document exists, show reader view
  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="h-14 border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center">
          <h1 className="text-lg font-medium text-gray-900">CoRead</h1>
          <span className="mx-3 text-gray-300">|</span>
          <span className="text-sm text-gray-600 truncate max-w-md">
            {document.title || 'Untitled Document'}
          </span>
        </div>
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 border border-gray-200 rounded-md shadow-sm hover:shadow transition-all"
        >
          Discussions
        </button>
      </header>

      {/* Sidebar Overlay */}
      {isSidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/20 z-40"
            onClick={() => setIsSidebarOpen(false)}
          />
          <div className="fixed right-0 top-0 h-full w-116 bg-white shadow-lg z-50">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-base font-medium text-gray-900">All Threads</h2>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="overflow-auto h-[calc(100%-57px)]">
              <DiscussionList onSelect={handleThreadSelectFromSidebar} />
            </div>
          </div>
        </>
      )}

      {/* Main Content */}
      <div ref={containerRef} className="flex-1 flex overflow-hidden">
        {/* Left: Text Viewer */}
        <div className="overflow-hidden" style={{ width: `${leftPanelWidth}%` }}>
          <TextViewer onThreadClick={handleThreadSelect} />
        </div>

        {/* Resize Handle */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1.5 bg-gray-100 hover:bg-gray-300 cursor-col-resize transition-colors shrink-0 flex items-center justify-center"
        >
          <div className="w-0.5 h-8 bg-gray-300 rounded-full" />
        </div>

        {/* Right: Discussion Panel */}
        <div className="overflow-hidden" style={{ width: `${100 - leftPanelWidth}%` }}>
          {isLoadingThread ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-sm text-gray-500">Loading discussion...</div>
            </div>
          ) : selectedThread ? (
            <DiscussionDetail
              thread={selectedThread}
              onBack={handleBack}
              onSendMessage={handleSendMessage}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="text-4xl mb-4">💬</div>
              <h3 className="text-base font-medium text-gray-900 mb-2">
                Select a discussion
              </h3>
              <p className="text-sm text-gray-500 max-w-xs">
                Click on the 💬 or emoji icons in the text to view AI agent discussions about that passage.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
