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
  id?: string;
  alert_type: string;
  severity: string;
  patient_id?: string;
  room_id?: string;
  title: string;
  description?: string;
  status: string;
  triggered_at: string;
  metadata?: any;
}

interface GlobalActivityFeedProps {
  events: GlobalEvent[];
  alerts: Alert[];
  isLoading?: boolean;
  onPatientClick?: (patientId: number) => void;
  onAlertResolve?: (alertId: string) => void;
}

export default function GlobalActivityFeed({ events, alerts, isLoading = false, onPatientClick, onAlertResolve }: GlobalActivityFeedProps) {
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

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'border-red-600 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-blue-500 bg-blue-50',
      info: 'border-neutral-300 bg-neutral-50'
    };
    return colors[severity] || colors.info;
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
    <div className="bg-surface border border-neutral-200 h-full flex flex-col overflow-hidden rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b-2 border-neutral-950 flex-shrink-0">
        <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
          Live Activity Feed
        </h2>
      </div>

      {/* Alerts Section */}
      {isLoading ? (
        <div className="px-8 py-6 border-b-2 border-neutral-200 bg-neutral-50 flex-shrink-0">
          <div className="flex items-center gap-2 text-neutral-500">
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span className="text-sm font-light">Loading alerts...</span>
          </div>
        </div>
      ) : (() => {
        const activeAlerts = alerts.filter(a => a.status === 'active');
        return activeAlerts.length > 0 ? (
          <div className="border-b-2 border-accent-terra/30 bg-accent-terra/10 flex-shrink-0 shadow-inner">
            {/* Header */}
            <div className="px-6 py-3 bg-accent-terra/20 border-b border-accent-terra/30">
              <div className="flex items-center justify-between">
                <h3 className="text-accent-terra flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Active Alerts ({activeAlerts.length})
                </h3>
              </div>
            </div>
            
            {/* Alerts List */}
            <div className="space-y-0 max-h-80 overflow-y-auto">
              {activeAlerts.map((alert, i) => (
                <div
                  key={alert.id || i}
                  className={`border-l-4 ${getSeverityColor(alert.severity)} px-6 py-4 border-b border-neutral-200/50 last:border-b-0 bg-white hover:bg-neutral-50 transition-all`}
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* Left: Alert Info */}
                    <div 
                      className="flex-1 cursor-pointer"
                      onClick={() => {
                        if (alert.patient_id && onPatientClick) {
                          const patientNum = parseInt(alert.patient_id.replace(/\D/g, '')) || 0;
                          onPatientClick(patientNum);
                        }
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${
                          alert.severity === 'critical' ? 'bg-red-600 text-white' :
                          alert.severity === 'high' ? 'bg-orange-500 text-white' :
                          alert.severity === 'medium' ? 'bg-yellow-500 text-white' :
                          'bg-neutral-500 text-white'
                        }`}>
                          {alert.severity}
                        </span>
                        {alert.patient_id && (
                          <span className="text-neutral-950 text-xs font-semibold">
                            {alert.patient_id}
                          </span>
                        )}
                        {alert.room_id && !alert.room_id.includes('-') && (
                          <span className="text-neutral-500 text-xs">
                            • {alert.room_id}
                          </span>
                        )}
                        <span className="text-[10px] font-light text-neutral-400 font-mono ml-auto">
                          {formatTime(alert.triggered_at)}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-neutral-950 mb-1">{alert.title}</p>
                      {alert.description && (
                        <p className="text-xs font-light text-neutral-600">{alert.description}</p>
                      )}
                    </div>

                    {/* Right: Action Button */}
                    {onAlertResolve && alert.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAlertResolve(alert.id!);
                        }}
                        className="flex-shrink-0 px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 border border-primary-200 hover:border-primary-300 rounded transition-all"
                      >
                        Dealt With
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null;
      })()}

      {/* Consolidated Event Log */}
      <div className="flex-1 overflow-hidden">
        <div className="px-6 py-4 h-full overflow-y-auto">
          {events.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-slate-600">
                <p className="text-sm">No activity yet</p>
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
