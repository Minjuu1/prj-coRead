import { useState, useCallback } from 'react';
import {
  TextViewer,
  DiscussionList,
  DiscussionDetail,
  DocumentUpload,
} from './components';
import { useStore } from './store/useStore';
import { threadApi } from './services/api';
import type { Thread, Document, Section, Message } from './types';
import type { AgentId } from './constants/agents';
import type { ThreadListItem } from './services/api';

// Temporary user ID for development (later: implement login flow)
const DEV_USER_ID = 'dev_user_001';

function App() {
  const { document, setDocument, setSections, setThreads, setSelectedThreadId } =
    useStore();

  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [threadsData, setThreadsData] = useState<Thread[]>([]);
  const [isLoadingThread, setIsLoadingThread] = useState(false);

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
      setThreadsData(threads as Thread[]);
    },
    [setDocument, setSections, setThreads]
  );

  // Handle thread selection
  const handleThreadSelect = async (threadId: string) => {
    setSelectedThreadId(threadId);

    // First, try to find in local data
    const localThread = threadsData.find((t) => t.threadId === threadId);
    if (localThread) {
      setSelectedThread(localThread);
      return;
    }

    // If not found locally, fetch from API
    try {
      setIsLoadingThread(true);
      const thread = await threadApi.get(threadId);
      setSelectedThread(thread);
      // Add to local cache
      setThreadsData((prev) => [...prev, thread]);
    } catch (err) {
      console.error('[App] Failed to fetch thread:', err);
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

      // Update local cache
      setThreadsData((prev) =>
        prev.map((t) => (t.threadId === selectedThread.threadId ? updatedThread : t))
      );
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

  // If no document, show upload screen
  if (!document) {
    return <DocumentUpload userId={DEV_USER_ID} onComplete={handleUploadComplete} />;
  }

  // Document exists, show reader view
  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="h-14 border-b border-gray-200 flex items-center px-6 shrink-0">
        <h1 className="text-lg font-medium text-gray-900">CoRead</h1>
        <span className="mx-3 text-gray-300">|</span>
        <span className="text-sm text-gray-600 truncate max-w-md">
          {document.title || 'Untitled Document'}
        </span>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Text Viewer (60%) */}
        <div className="w-3/5 border-r border-gray-200 overflow-hidden">
          <TextViewer onThreadClick={handleThreadSelect} />
        </div>

        {/* Right: Discussion Panel (40%) */}
        <div className="w-2/5 overflow-hidden">
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
            <DiscussionList onSelect={handleThreadSelect} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
