import React, { useMemo } from 'react';
import { MessageSquare } from 'lucide-react';
import { useStore } from '../store/useStore';
import { AGENTS, type AgentId } from '../constants/agents';
import { COLORS } from '../constants/colors';
import type { Section } from '../types';
import type { ThreadListItem } from '../services/api';

interface TextViewerProps {
  onThreadClick: (threadId: string) => void;
}

// Thread with computed offsets
interface ThreadWithOffset extends ThreadListItem {
  computedStart: number;
  computedEnd: number;
}

export const TextViewer: React.FC<TextViewerProps> = ({ onThreadClick }) => {
  const { sections, threads, selectedThreadId } = useStore();

  // Group threads by section and compute actual offsets from snippetText
  const threadsBySection = useMemo(() => {
    const map: Record<string, ThreadWithOffset[]> = {};

    threads.forEach((thread) => {
      const sectionId = thread.anchor.sectionId;
      const section = sections.find((s) => s.sectionId === sectionId);

      if (!section) return;

      // Find snippetText in section content
      const snippetText = thread.anchor.snippetText;
      const startOffset = section.content.indexOf(snippetText);

      if (startOffset === -1) {
        console.warn(`Could not find snippet in section: "${snippetText.slice(0, 50)}..."`);
        return;
      }

      const endOffset = startOffset + snippetText.length;

      if (!map[sectionId]) {
        map[sectionId] = [];
      }

      map[sectionId].push({
        ...thread,
        computedStart: startOffset,
        computedEnd: endOffset,
      });
    });

    // Sort by offset within each section
    Object.values(map).forEach((arr) => {
      arr.sort((a, b) => a.computedStart - b.computedStart);
    });

    return map;
  }, [threads, sections]);

  if (sections.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No document loaded
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        {sections.map((section) => (
          <SectionView
            key={section.sectionId}
            section={section}
            threads={threadsBySection[section.sectionId] || []}
            selectedThreadId={selectedThreadId}
            onThreadClick={onThreadClick}
          />
        ))}
      </div>
    </div>
  );
};

interface SectionViewProps {
  section: Section;
  threads: ThreadWithOffset[];
  selectedThreadId: string | null;
  onThreadClick: (threadId: string) => void;
}

const SectionView: React.FC<SectionViewProps> = ({
  section,
  threads,
  selectedThreadId,
  onThreadClick,
}) => {
  // Render content with highlights and thread buttons
  const renderContent = () => {
    if (threads.length === 0) {
      return (
        <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
          {section.content}
        </p>
      );
    }

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    threads.forEach((thread, idx) => {
      const startOffset = thread.computedStart;
      const endOffset = thread.computedEnd;

      // Add text before this highlight
      if (startOffset > lastIndex) {
        elements.push(
          <span key={`text-${idx}`}>
            {section.content.slice(lastIndex, startOffset)}
          </span>
        );
      }

      // Add highlighted text with button
      const isSelected = thread.threadId === selectedThreadId;
      const highlightStyle = isSelected
        ? { backgroundColor: COLORS.highlight }
        : {};

      elements.push(
        <span
          key={`highlight-${idx}`}
          className="relative inline"
          style={highlightStyle}
        >
          {section.content.slice(startOffset, endOffset)}
          <ThreadButton
            thread={thread}
            isSelected={isSelected}
            onClick={() => onThreadClick(thread.threadId)}
          />
        </span>
      );

      lastIndex = endOffset;
    });

    // Add remaining text
    if (lastIndex < section.content.length) {
      elements.push(
        <span key="text-end">{section.content.slice(lastIndex)}</span>
      );
    }

    return (
      <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
        {elements}
      </p>
    );
  };

  return (
    <div className="mb-8">
      <h2 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b border-gray-200">
        {section.title}
      </h2>
      {renderContent()}
    </div>
  );
};

interface ThreadButtonProps {
  thread: ThreadListItem;
  isSelected: boolean;
  onClick: () => void;
}

const ThreadButton: React.FC<ThreadButtonProps> = ({
  thread,
  isSelected,
  onClick,
}) => {
  const isDiscussion = thread.threadType === 'discussion';

  if (isDiscussion) {
    return (
      <button
        onClick={onClick}
        className={`
          inline-flex items-center justify-center
          w-6 h-6 ml-1 -mb-1
          rounded border
          text-xs
          transition-colors
          ${
            isSelected
              ? 'bg-gray-200 border-gray-400'
              : 'bg-gray-100 border-gray-200 hover:bg-gray-200'
          }
        `}
        title={thread.tensionPoint}
      >
        <MessageSquare size={14} className="text-gray-600" />
      </button>
    );
  }

  // Comment - show agent color dot
  const agentId = thread.participants[0] as AgentId;
  const agent = AGENTS[agentId];

  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center justify-center
        w-6 h-6 ml-1 -mb-1
        rounded border
        transition-colors
        ${
          isSelected
            ? 'bg-gray-200 border-gray-400'
            : 'bg-white border-gray-200 hover:bg-gray-50'
        }
      `}
      title={`${agent.name}: ${thread.tensionPoint}`}
    >
      <span
        className="w-2.5 h-2.5 rounded-full"
        style={{ backgroundColor: agent.color }}
      />
    </button>
  );
};

export default TextViewer;
