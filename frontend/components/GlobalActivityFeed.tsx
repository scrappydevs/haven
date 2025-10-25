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

interface Alert {
  patient_id: number;
  message: string;
  crs_score: number;
  heart_rate: number;
  timestamp: string;
}

interface GlobalActivityFeedProps {
  events: GlobalEvent[];
  alerts: Alert[];
  onPatientClick?: (patientId: number) => void;
}

export default function GlobalActivityFeed({ events, alerts, onPatientClick }: GlobalActivityFeedProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getLogColor = (type: string) => {
    const styles: Record<string, string> = {
      alert: 'text-red-500',
      threshold: 'text-orange-400',
      behavior: 'text-yellow-400',
      seizure: 'text-purple-400',
      vital: 'text-cyan-400',
      system: 'text-green-400',
      monitoring: 'text-blue-400',
      warning: 'text-yellow-400'
    };
    return styles[type] || 'text-blue-400';
  };

  const getLogPrefix = (type: string) => {
    const prefixes: Record<string, string> = {
      alert: '[ALERT]',
      threshold: '[WARN ]',
      behavior: '[EVENT]',
      seizure: '[ALERT]',
      vital: '[VITAL]',
      system: '[SYS  ]',
      monitoring: '[INFO ]',
      warning: '[WARN ]'
    };
    return prefixes[type] || '[INFO ]';
  };

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700 h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-700 flex-shrink-0">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-2xl">📡</span>
          Live Activity Feed
        </h2>
        <p className="text-sm text-slate-400">All active streams • Real-time</p>
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="px-6 py-4 border-b border-slate-700 bg-red-500/5 flex-shrink-0">
          <h3 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
            <span className="text-lg">🚨</span>
            Active Alerts ({alerts.length})
          </h3>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {alerts.map((alert, i) => (
              <div
                key={i}
                className="bg-red-500/10 border border-red-500/30 rounded p-3 cursor-pointer hover:bg-red-500/20 transition-colors"
                onClick={() => onPatientClick && onPatientClick(alert.patient_id)}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-red-400">
                    Patient #{alert.patient_id}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatTime(alert.timestamp)}
                  </span>
                </div>
                <p className="text-xs text-red-300">{alert.message}</p>
                <div className="flex gap-3 mt-1 text-xs text-slate-400">
                  <span>CRS: {(alert.crs_score * 100).toFixed(0)}%</span>
                  <span>HR: {alert.heart_rate} bpm</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Consolidated Event Log */}
      <div className="flex-1 overflow-hidden">
        <div className="px-6 py-4 h-full overflow-y-auto">
          {events.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-slate-600">
                <p className="text-4xl mb-2">👀</p>
                <p className="text-sm">No activity yet</p>
                <p className="text-xs mt-1">Events will appear here when patients are monitored</p>
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
                  className="border-l-2 border-slate-700 pl-3 py-2 hover:border-blue-500 hover:bg-slate-700/30 transition-all cursor-pointer rounded-r"
                  onClick={() => onPatientClick && onPatientClick(event.patientId)}
                >
                  {/* First line: time + prefix + patient name */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-slate-500">{formatTime(event.timestamp)}</span>
                    <span className={`${getLogColor(event.type)} font-bold`}>
                      {getLogPrefix(event.type)}
                    </span>
                    <span className="font-semibold text-blue-400">{event.patientName}</span>
                  </div>

                  {/* Second line: message */}
                  <div className="flex items-start gap-2 ml-20">
                    <span className="text-slate-600">└─</span>
                    <span className={getLogColor(event.type)}>
                      {event.message.replace(/[🚨⚠️⚡👋🔄❤️📹👁️✓]/g, '').trim()}
                    </span>
                  </div>

                  {/* Third line: details */}
                  <div className="ml-24 text-slate-500 text-[10px] mt-0.5">
                    {event.details}
                  </div>
                </motion.div>
              ))}

              {/* Monitoring indicator */}
              <div className="flex items-center gap-2 mt-4 text-green-500 border-l-2 border-green-500/30 pl-3 py-2">
                <span className="animate-pulse">▊</span>
                <span className="text-slate-600 text-xs">System monitoring active...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
