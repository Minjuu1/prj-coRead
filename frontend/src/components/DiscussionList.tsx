import React from 'react';
import { MessageSquare } from 'lucide-react';
import { useStore } from '../store/useStore';
import { AGENTS, type AgentId } from '../constants/agents';
import { DISCUSSION_TYPES, type DiscussionType } from '../constants/discussion';
import type { ThreadListItem } from '../services/api';

interface DiscussionListProps {
  onSelect: (threadId: string) => void;
}

export const DiscussionList: React.FC<DiscussionListProps> = ({ onSelect }) => {
  const { threads, selectedThreadId } = useStore();

  if (threads.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <p className="text-gray-500 text-sm">No discussions yet</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-base font-medium text-gray-900">Discussions</h2>
        <p className="text-xs text-gray-500 mt-1">{threads.length} threads</p>
      </div>

      <div className="divide-y divide-gray-100">
        {threads.map((thread) => (
          <ThreadListItemView
            key={thread.threadId}
            thread={thread}
            isSelected={thread.threadId === selectedThreadId}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
};

interface ThreadListItemViewProps {
  thread: ThreadListItem;
  isSelected: boolean;
  onSelect: (threadId: string) => void;
}

const ThreadListItemView: React.FC<ThreadListItemViewProps> = ({
  thread,
  isSelected,
  onSelect,
}) => {
  const isDiscussion = thread.threadType === 'discussion';
  const discussionType = thread.discussionType as DiscussionType | undefined;

  return (
    <button
      onClick={() => onSelect(thread.threadId)}
      className={`
        w-full text-left p-4 transition-colors
        ${isSelected ? 'bg-gray-100' : 'hover:bg-gray-50'}
      `}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        {isDiscussion ? (
          <div className="w-6 h-6 rounded bg-gray-100 border border-gray-200 flex items-center justify-center">
            <MessageSquare size={14} className="text-gray-600" />
          </div>
        ) : (
          <AgentDot agentId={thread.participants[0] as AgentId} />
        )}

        <span className="text-xs text-gray-500">
          {isDiscussion ? 'Discussion' : 'Comment'}
        </span>

        {discussionType && (
          <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
            {DISCUSSION_TYPES[discussionType]?.label || discussionType}
          </span>
        )}
      </div>

      {/* Tension Point */}
      <p className="text-sm text-gray-900 line-clamp-2 mb-2">
        {thread.tensionPoint}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          {thread.participants.map((agentId) => (
            <AgentDot key={agentId} agentId={agentId as AgentId} size="small" />
          ))}
        </div>

        <span className="text-xs text-gray-400">
          {thread.messageCount} {thread.messageCount === 1 ? 'msg' : 'msgs'}
        </span>
      </div>
    </button>
  );
};

interface AgentDotProps {
  agentId: AgentId;
  size?: 'small' | 'normal';
}

const AgentDot: React.FC<AgentDotProps> = ({ agentId, size = 'normal' }) => {
  const agent = AGENTS[agentId];
  const sizeClass = size === 'small' ? 'w-4 h-4' : 'w-6 h-6';
  const dotSize = size === 'small' ? 'w-2 h-2' : 'w-2.5 h-2.5';

  return (
    <div
      className={`${sizeClass} rounded bg-white border border-gray-200 flex items-center justify-center`}
      title={agent.name}
    >
      <span
        className={`${dotSize} rounded-full`}
        style={{ backgroundColor: agent.color }}
      />
    </div>
  );
};

export default DiscussionList;
