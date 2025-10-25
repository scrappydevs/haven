'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TerminalLogEntry {
  id: number;
  timestamp: Date;
  type: 'vital' | 'agent_thinking' | 'agent_action' | 'monitoring' | 'alert';
  severity: 'normal' | 'warning' | 'critical';
  message: string;
  details?: string;
  icon?: string;
  highlight?: boolean;
  metadata?: {
    value?: number;
    change?: number;
    confidence?: number;
  };
}

interface TerminalLogProps {
  entries: TerminalLogEntry[];
  maxHeight?: string;
}

export default function TerminalLog({ entries, maxHeight = '500px' }: TerminalLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries added
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries]);

  const getTextColor = (type: string, severity: string) => {
    if (type === 'agent_action') return 'text-cyan-400';
    if (type === 'agent_thinking') return 'text-blue-400';
    if (type === 'alert') return 'text-red-400';

    switch (severity) {
      case 'critical': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-green-400';
    }
  };

  const getBgColor = (highlight?: boolean) => {
    if (highlight) return 'bg-cyan-500/10 border-l-2 border-cyan-400';
    return '';
  };

  const formatTimestamp = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  const formatChange = (change?: number) => {
    if (!change) return '';
    const sign = change > 0 ? '↑' : '↓';
    const value = Math.abs(change);
    return ` ${sign} (${change > 0 ? '+' : ''}${value})`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Terminal Header */}
      <div className="bg-neutral-900 border-b border-neutral-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span className="font-mono text-xs text-neutral-400">PATIENT_GUARDIAN_AGENT</span>
        </div>
        <span className="font-mono text-xs text-neutral-500">
          {entries.length} events
        </span>
      </div>

      {/* Terminal Content */}
      <div
        className="bg-neutral-950 p-4 font-mono text-sm overflow-y-auto"
        style={{ maxHeight }}
      >
        <AnimatePresence initial={false}>
          {entries.map((entry) => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className={`py-1.5 px-2 ${getBgColor(entry.highlight)}`}
            >
              {/* Main line */}
              <div className="flex items-start gap-2">
                {/* Timestamp */}
                <span className="text-neutral-600 flex-shrink-0">
                  [{formatTimestamp(entry.timestamp)}]
                </span>

                {/* Icon */}
                {entry.icon && (
                  <span className="flex-shrink-0">{entry.icon}</span>
                )}

                {/* Message */}
                <span className={getTextColor(entry.type, entry.severity)}>
                  {entry.message}
                  {entry.metadata?.change && (
                    <span className={entry.metadata.change > 0 ? 'text-red-400' : 'text-green-400'}>
                      {formatChange(entry.metadata.change)}
                    </span>
                  )}
                  {entry.metadata?.value && (
                    <span className="text-neutral-400">
                      {' '}[{entry.metadata.value}]
                    </span>
                  )}
                </span>
              </div>

              {/* Details line (if present) */}
              {entry.details && (
                <div className="ml-16 mt-1 text-neutral-500 text-xs">
                  {entry.details}
                </div>
              )}

              {/* Confidence bar (if present) */}
              {entry.metadata?.confidence !== undefined && (
                <div className="ml-16 mt-2 flex items-center gap-2">
                  <span className="text-neutral-600 text-xs">Confidence:</span>
                  <div className="flex-1 max-w-[200px] h-1.5 bg-neutral-800">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${entry.metadata.confidence * 100}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full ${
                        entry.metadata.confidence > 0.8 ? 'bg-green-500' :
                        entry.metadata.confidence > 0.6 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                    />
                  </div>
                  <span className="text-neutral-400 text-xs">
                    {(entry.metadata.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty state */}
        {entries.length === 0 && (
          <div className="text-neutral-600 text-center py-8">
            <div className="mb-2">$ waiting for events...</div>
            <div className="animate-pulse">_</div>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Terminal Footer */}
      <div className="bg-neutral-900 border-t border-neutral-700 px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-neutral-400 font-mono">ACTIVE</span>
          </div>
          <span className="text-neutral-600">|</span>
          <span className="text-neutral-500 font-mono">Real-time monitoring</span>
        </div>
        <span className="text-neutral-600 font-mono text-xs">
          Press ⌘K for shortcuts
        </span>
      </div>
    </div>
  );
}
