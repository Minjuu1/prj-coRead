import React, { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Send, RotateCw } from 'lucide-react';
import { AGENTS, type AgentId } from '../constants/agents';
import type { Thread, Message } from '../types';

interface DiscussionDetailProps {
  thread: Thread;
  onBack: () => void;
  onSendMessage: (content: string, taggedAgent?: AgentId) => void;
  onGenerateMore?: () => void;
  isAgentThinking?: boolean;
  isGeneratingMore?: boolean;
}

export const DiscussionDetail: React.FC<DiscussionDetailProps> = ({
  thread,
  onBack,
  onSendMessage,
  onGenerateMore,
  isAgentThinking = false,
  isGeneratingMore = false,
}) => {
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change or when thinking
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread.messages, isAgentThinking, isGeneratingMore]);

  const handleSend = async () => {
    if (!messageInput.trim() || isSending) return;

    setIsSending(true);
    try {
      // Extract tagged agent from message (e.g., @Instrumental)
      const tagMatch = messageInput.match(/@(instrumental|critical|aesthetic)/i);
      const taggedAgent = tagMatch
        ? (tagMatch[1].toLowerCase() as AgentId)
        : undefined;

      await onSendMessage(messageInput, taggedAgent);
      setMessageInput('');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Shift+Enter for new line, Enter alone does nothing (use button)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
    }
  };

  const isDiscussion = thread.threadType === 'discussion';
  const isLoading = isAgentThinking || isGeneratingMore;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-3"
        >
          <ArrowLeft size={14} />
          Close
        </button>

        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-gray-500">
            {isDiscussion ? 'Discussion' : 'Comment'}
          </span>
        </div>

        {/* Anchor context */}
        <p className="text-sm text-gray-700 italic border-l-2 border-gray-300 pl-3 mb-3">
          "{thread.anchor.snippetText}"
        </p>

        {/* Participants */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Participants:</span>
          {thread.participants.map((agentId) => (
            <AgentBadge key={agentId} agentId={agentId} />
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 bg-gray-50">
        <div className="space-y-4">
          {thread.messages.map((message) => (
            <MessageView key={message.messageId} message={message} />
          ))}

          {/* Thinking indicator */}
          {isAgentThinking && (
            <ThinkingIndicator participants={thread.participants} />
          )}
          {isGeneratingMore && (
            <ThinkingIndicator participants={thread.participants} label="Generating more turns" />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Generate More button */}
        {isDiscussion && onGenerateMore && (
          <div className="flex justify-center mt-4">
            <button
              onClick={onGenerateMore}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-white hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCw size={14} className={isGeneratingMore ? 'animate-spin' : ''} />
              Generate More
            </button>
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message... (use @Instrumental, @Critical, or @Aesthetic to tag)"
            className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-md resize-none focus:outline-none focus:border-gray-400"
            rows={2}
            disabled={isSending || isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!messageInput.trim() || isSending || isLoading}
            className="px-4 py-2 bg-gray-900 text-white text-sm rounded-md hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

const ThinkingIndicator: React.FC<{ participants: string[]; label?: string }> = ({
  participants,
  label = 'Agents are thinking',
}) => (
  <div className="flex items-center gap-2 px-3 py-2">
    <div className="flex -space-x-1">
      {participants.map((agentId) => {
        const agent = AGENTS[agentId as AgentId];
        if (!agent) return null;
        return (
          <div
            key={agentId}
            className="w-5 h-5 rounded-full border-2 border-white flex items-center justify-center text-[10px]"
            style={{ backgroundColor: agent.colorLight }}
          >
            {agent.emoji}
          </div>
        );
      })}
    </div>
    <span className="text-xs text-gray-400">{label}</span>
    <span className="flex gap-0.5">
      <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  </div>
);

interface MessageViewProps {
  message: Message;
}

const MessageView: React.FC<MessageViewProps> = ({ message }) => {
  const isUser = message.author === 'user';
  const agent = !isUser ? AGENTS[message.author as AgentId] : null;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'order-1' : 'order-1'}`}>
        {/* Author label */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {isUser ? (
            <span className="text-xs font-medium text-gray-500">You</span>
          ) : (
            <div className="flex items-center gap-1">
              <span className="text-sm">{agent?.emoji}</span>
              <span
                className="text-xs font-medium"
                style={{ color: agent?.color }}
              >
                {agent?.name}
              </span>
            </div>
          )}
          <span className="text-xs text-gray-400">
            {formatTime(message.timestamp)}
          </span>
        </div>

        {/* Message bubble */}
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-gray-900 text-white rounded-br-md'
              : 'rounded-bl-md'
          }`}
          style={
            !isUser
              ? {
                  backgroundColor: agent?.colorLight,
                }
              : undefined
          }
        >
          <p className={`text-sm whitespace-pre-wrap leading-relaxed ${isUser ? 'text-white' : 'text-gray-800'}`}>
            {message.content}
          </p>

          {/* References */}
          {message.references.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200/30">
              {message.references.map((ref, idx) => (
                <blockquote
                  key={idx}
                  className={`text-xs italic pl-2 mt-1 ${
                    isUser ? 'text-gray-300 border-l-2 border-gray-600' : 'text-gray-600 border-l-2 border-gray-400'
                  }`}
                >
                  "{ref.text}"
                </blockquote>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface AgentBadgeProps {
  agentId: AgentId;
}

const AgentBadge: React.FC<AgentBadgeProps> = ({ agentId }) => {
  const agent = AGENTS[agentId];

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs"
      style={{
        backgroundColor: agent.colorLight,
        color: agent.color,
      }}
    >
      <span>{agent.emoji}</span>
      {agent.name}
    </span>
  );
};

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default DiscussionDetail;
