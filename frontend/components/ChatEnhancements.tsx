'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface CopyButtonProps {
  text: string;
}

export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1.5 bg-neutral-700 hover:bg-neutral-600 text-white text-xs rounded transition-colors opacity-0 group-hover:opacity-100"
      title="Copy to clipboard"
    >
      {copied ? (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

interface ToolUseIndicatorProps {
  toolCount: number;
}

export function ToolUseIndicator({ toolCount }: ToolUseIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="flex justify-start mb-2"
    >
      <div className="flex items-center gap-2 px-3 py-2 bg-primary-50 border border-primary-200 text-primary-700 text-xs rounded-lg">
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
        </svg>
        <span>Fetching data from database ({toolCount} {toolCount === 1 ? 'query' : 'queries'})</span>
      </div>
    </motion.div>
  );
}

interface FollowUpQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export function FollowUpQuestions({ questions, onSelect }: FollowUpQuestionsProps) {
  if (questions.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="mt-3 space-y-1.5"
    >
      <p className="text-xs font-light text-neutral-950 uppercase tracking-wider mb-2">
        Follow-up
      </p>
      {questions.map((q, i) => (
        <button
          key={i}
          onClick={() => onSelect(q)}
          className="w-full text-left px-3 py-2 text-sm font-light text-neutral-600 bg-neutral-50 hover:bg-neutral-100 border border-neutral-200 transition-colors"
          style={{ borderRadius: '6px' }}
        >
          {q}
        </button>
      ))}
    </motion.div>
  );
}

interface ExportButtonProps {
  messages: any[];
  sessionTitle: string | null;
}

export function ExportButton({ messages, sessionTitle }: ExportButtonProps) {
  const handleExport = () => {
    const exportText = messages.map(m => 
      `[${m.role.toUpperCase()}]: ${m.content}`
    ).join('\n\n');
    
    const blob = new Blob([`# ${sessionTitle || 'Haven AI Chat'}\n\n${exportText}`], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `haven-chat-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleExport}
      className="text-neutral-400 hover:text-neutral-950 transition-colors"
      title="Export chat"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
    </button>
  );
}

