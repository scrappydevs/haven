'use client';

import { motion } from 'framer-motion';

interface GlobalEvent {
  timestamp: string;
  patientId: number;
  patientName: string;
  type: string;
  severity: string;
  message: string;
  details: string;
}

interface GlobalActivityFeedProps {
  events: GlobalEvent[];
  onPatientClick?: (patientId: number) => void;
}

export default function GlobalActivityFeed({ events, onPatientClick }: GlobalActivityFeedProps) {
  const formatTime = (timestamp: string) => {
    if (!timestamp) return '--:--:--';
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch (e) {
      return '--:--:--';
    }
  };

  const getRelativeTime = (timestamp: string) => {
    if (!timestamp) return '';
    try {
      const now = new Date();
      const eventTime = new Date(timestamp);
      const diffMs = now.getTime() - eventTime.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${diffDays}d ago`;
    } catch (e) {
      return '';
    }
  };

  const getLogPrefix = (type: string) => {
    const prefixes: Record<string, string> = {
      alert: '[ALERT]',
      threshold: '[WARN ]',
      behavior: '[EVENT]',
      seizure: '[ALERT]',
      vital: '[VITAL]',
      system: '[SYS  ]',
      monitoring: '[INFO]',
      warning: '[WARN]'
    };
    return prefixes[type] || '[INFO]';
  };

  return (
    <div className="bg-surface border border-neutral-200 h-full flex flex-col overflow-hidden rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b-2 border-neutral-950 flex-shrink-0">
        <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
          Live Activity Feed
        </h2>
      </div>

      {/* Consolidated Event Log */}
      <div className="flex-1 overflow-hidden">
        <div className="px-6 py-4 h-full overflow-y-auto">
          {events.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-neutral-500">
                <p className="text-sm font-light">No activity yet</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {events.map((event, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-l-2 border-neutral-300 pl-3 py-2 hover:border-primary-700 hover:bg-neutral-50 transition-all cursor-pointer rounded-r"
                  onClick={() => onPatientClick && onPatientClick(event.patientId)}
                >
                  {/* First line: time + prefix + patient name */}
                  <div className="flex items-start gap-2 mb-1">
                    <div className="flex flex-col">
                      <span className="text-neutral-400 font-mono text-[10px]">{formatTime(event.timestamp)}</span>
                      <span className="text-neutral-400 font-mono text-[9px]">{getRelativeTime(event.timestamp)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-light text-neutral-950 font-mono">
                        {getLogPrefix(event.type)}
                      </span>
                      <span className="text-xs font-light text-neutral-950">{event.patientName}</span>
                    </div>
                  </div>

                  {/* Second line: message */}
                  <div className="flex items-start gap-2 ml-20">
                    <span className="text-neutral-400 text-[10px]">└─</span>
                    <span className="text-xs font-light text-neutral-950">
                      {event.message.replace(/[🚨⚠️⚡👋🔄❤️📹👁️✓]/g, '').trim()}
                    </span>
                  </div>

                  {/* Third line: details */}
                  <div className="ml-24 text-neutral-500 text-[10px] mt-0.5 font-light">
                    {event.details}
                  </div>
                </motion.div>
              ))}

              {/* Monitoring indicator */}
              <div className="flex items-center gap-2 mt-4 text-green-500 border-l-2 border-green-500/30 pl-3 py-2">
                <span className="animate-pulse">▊</span>
                <span className="text-neutral-500 text-xs font-light">System monitoring active...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
