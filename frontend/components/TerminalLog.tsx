'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TerminalLogEntry {
  id: number;
  timestamp: Date;
  type: 'vital' | 'agent_thinking' | 'agent_action' | 'agent_reasoning' | 'monitoring' | 'alert';
  severity: 'normal' | 'warning' | 'critical';
  message: string;
  details?: string;
  icon?: string;
  highlight?: boolean;
  metadata?: {
    value?: number;
    change?: number;
    confidence?: number;
    concerns?: string[];
  };
}

interface TerminalLogProps {
  entries: TerminalLogEntry[];
  analysisMode?: 'normal' | 'enhanced';
}

export default function TerminalLog({ entries, analysisMode = 'enhanced' }: TerminalLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries added
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries]);

  const getTextColor = (type: string, severity: string) => {
    // Agent message types
    if (type === 'agent_thinking') return 'text-primary-700';  // Mint green for analyzing
    if (type === 'agent_reasoning') return 'text-primary-700';  // Mint green for Claude reasoning
    if (type === 'agent_action') return 'text-primary-700';   // Mint green for actions taken
    if (type === 'alert') return 'text-accent-terra';            // Terracotta for critical alerts

    // Vital signs based on severity
    switch (severity) {
      case 'critical': return 'text-accent-terra';      // Terracotta for critical vitals
      case 'warning': return 'text-yellow-600';    // Yellow for elevated vitals
      default: return 'text-primary-700';            // Mint green for normal
    }
  };

  const getBgColor = (type: string, highlight?: boolean) => {
    if (type === 'agent_reasoning') return 'bg-primary-400/10 border-l-2 border-primary-700';
    if (type === 'agent_action') return 'bg-primary-400/10 border-l-2 border-primary-700';
    if (highlight) return 'bg-primary-400/10 border-l-2 border-primary-700';
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Terminal Header - Minimal */}
      <div className="bg-neutral-50 border-b border-neutral-200 px-3 py-1.5 flex items-center justify-between" style={{ flexShrink: 0 }}>
        <span className="font-mono text-xs text-primary-700">FETCH_AI_HEALTH_AGENT</span>
        <span className="font-mono text-xs text-neutral-500">
          {entries.length} events
        </span>
      </div>

      {/* Terminal Content - Fixed height with scroll */}
      <div
        className="bg-surface p-3 font-mono text-xs"
        style={{
          flex: '1 1 0',
          overflowY: 'auto',
          minHeight: 0
        }}
      >
        <AnimatePresence initial={false}>
          {entries.map((entry) => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className={`py-1 px-2 ${getBgColor(entry.type, entry.highlight)}`}
            >
              {/* Main line */}
              <div className="flex items-start gap-2">
                {/* Timestamp */}
                <span className="text-neutral-500 flex-shrink-0">
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
                    <span className={entry.metadata.change > 0 ? 'text-accent-terra' : 'text-primary-700'}>
                      {formatChange(entry.metadata.change)}
                    </span>
                  )}
                  {entry.metadata?.value && (
                    <span className="text-neutral-600">
                      {' '}[{entry.metadata.value}]
                    </span>
                  )}
                </span>
              </div>

              {/* Details line (if present) */}
              {entry.details && (
                <div className="ml-14 mt-0.5 text-neutral-600" style={{ fontSize: '0.7rem' }}>
                  {entry.details}
                </div>
              )}

              {/* Concerns (for agent reasoning) */}
              {entry.metadata?.concerns && entry.metadata.concerns.length > 0 && (
                <div className="ml-14 mt-0.5 text-neutral-700" style={{ fontSize: '0.7rem' }}>
                  Concerns: [{entry.metadata.concerns.join(', ')}]
                </div>
              )}

              {/* Confidence bar (if present) */}
              {entry.metadata?.confidence !== undefined && (
                <div className="ml-14 mt-1 flex items-center gap-2">
                  <span className="text-neutral-600" style={{ fontSize: '0.65rem' }}>Confidence:</span>
                  <div className="flex-1 max-w-[150px] h-1 bg-neutral-200">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${entry.metadata.confidence * 100}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full ${
                        entry.metadata.confidence > 0.8 ? 'bg-primary-700' :
                        entry.metadata.confidence > 0.6 ? 'bg-yellow-600' :
                        'bg-accent-terra'
                      }`}
                    />
                  </div>
                  <span className="text-neutral-600" style={{ fontSize: '0.65rem' }}>
                    {(entry.metadata.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty state or Analysis Disabled */}
        {entries.length === 0 && (
          <div className="text-neutral-500 text-center py-4">
            {analysisMode === 'normal' ? (
              <>
                <div className="mb-2">
                  <svg className="w-6 h-6 mx-auto text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                </div>
                <div className="mb-1 text-xs font-semibold text-neutral-600">Analysis Disabled</div>
                <div className="text-xs text-neutral-500">Stream is in Normal Mode</div>
                <div className="text-xs text-neutral-500 mt-2">No AI/CV analysis active</div>
              </>
            ) : (
              <>
                <div className="mb-1 text-xs">$ waiting for events...</div>
                <div className="animate-pulse text-xs">_</div>
              </>
            )}
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={bottomRef} className="h-1" />
      </div>
    </div>
  );
}
