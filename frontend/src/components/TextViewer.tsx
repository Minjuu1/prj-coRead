import React, { useMemo, useEffect, useRef, useState } from 'react';
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
      <div className="max-w-3xl">
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
  const [buttonPositions, setButtonPositions] = useState<Record<string, number>>({});
  const highlightRefs = useRef<Record<string, HTMLSpanElement | null>>({});
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate button positions after render
  useEffect(() => {
    const updatePositions = () => {
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const positions: Record<string, number> = {};

      threads.forEach((thread) => {
        const el = highlightRefs.current[thread.threadId];
        if (el) {
          const rect = el.getBoundingClientRect();
          positions[thread.threadId] = rect.top - containerRect.top;
        }
      });

      setButtonPositions(positions);
    };

    updatePositions();
    window.addEventListener('resize', updatePositions);
    return () => window.removeEventListener('resize', updatePositions);
  }, [threads, section.content]);

  // Render text with markdown-style headers (### ) styled as subsection headers
  const renderTextWithHeaders = (text: string, keyPrefix: string) => {
    // Split by lines that start with ###
    const parts = text.split(/(\n### [^\n]+)/);

    return parts.map((part, i) => {
      if (part.startsWith('\n### ')) {
        // Subsection header
        const headerText = part.slice(5); // Remove '\n### '
        return (
          <React.Fragment key={`${keyPrefix}-${i}`}>
            {'\n'}
            <span className="font-medium text-gray-800 text-base">
              {headerText}
            </span>
          </React.Fragment>
        );
      }
      // Regular text
      return <React.Fragment key={`${keyPrefix}-${i}`}>{part}</React.Fragment>;
    });
  };

  // Render content with highlights (no buttons inside)
  const renderContent = () => {
    if (threads.length === 0) {
      return (
        <div className="text-gray-900 leading-relaxed whitespace-pre-wrap">
          {renderTextWithHeaders(section.content, 'content')}
        </div>
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
            {renderTextWithHeaders(section.content.slice(lastIndex, startOffset), `text-${idx}`)}
          </span>
        );
      }

      // Add highlighted text (no button here)
      const isSelected = thread.threadId === selectedThreadId;
      const highlightStyle = isSelected
        ? { backgroundColor: COLORS.highlight }
        : {};

      elements.push(
        <span
          key={`highlight-${idx}`}
          ref={(el) => { highlightRefs.current[thread.threadId] = el; }}
          style={highlightStyle}
        >
          {renderTextWithHeaders(section.content.slice(startOffset, endOffset), `highlight-${idx}`)}
        </span>
      );

      lastIndex = endOffset;
    });

    // Add remaining text
    if (lastIndex < section.content.length) {
      elements.push(
        <span key="text-end">
          {renderTextWithHeaders(section.content.slice(lastIndex), 'text-end')}
        </span>
      );
    }

    return (
      <div className="text-gray-900 leading-relaxed whitespace-pre-wrap">
        {elements}
      </div>
    );
  };

  return (
    <div className="mb-8">
      <h2 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b border-gray-200">
        {section.title}
      </h2>
      <div ref={containerRef} className="flex">
        {/* Text content */}
        <div className="flex-1">
          {renderContent()}
        </div>

        {/* Button column */}
        <div className="w-12 relative shrink-0">
          {threads.map((thread) => (
            <ThreadButton
              key={thread.threadId}
              thread={thread}
              isSelected={thread.threadId === selectedThreadId}
              onClick={() => {
                console.log('[TextViewer] Button clicked, threadId:', thread.threadId);
                onThreadClick(thread.threadId);
              }}
              top={buttonPositions[thread.threadId] ?? 0}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

interface ThreadButtonProps {
  thread: ThreadListItem;
  isSelected: boolean;
  onClick: () => void;
  top: number;
}

const ThreadButton: React.FC<ThreadButtonProps> = ({
  thread,
  isSelected,
  onClick,
  top,
}) => {
  const isDiscussion = thread.threadType === 'discussion';
  const agentId = thread.participants[0] as AgentId;
  const agent = AGENTS[agentId];

  const baseClasses = `
    absolute left-2
    w-8 h-8
    inline-flex items-center justify-center
    text-base
    rounded-full
    border border-gray-200
    bg-white
    shadow-sm
    hover:shadow-md
    hover:border-gray-300
    transition-all
    cursor-pointer
    z-10
    ${isSelected ? 'ring-2 ring-amber-300 border-amber-300 shadow-md' : ''}
  `;

  if (isDiscussion) {
    return (
      <button
        onClick={onClick}
        className={baseClasses}
        style={{ top }}
        title={thread.tensionPoint}
      >
        💬
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={baseClasses}
      style={{ top }}
      title={`${agent.name}: ${thread.tensionPoint}`}
    >
      {agent.emoji}
    </button>
  );
};

export default TextViewer;
