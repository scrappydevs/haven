'use client';

import { motion, AnimatePresence } from 'framer-motion';

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

interface AlertsModalProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: Alert[];
  onAlertResolve?: (alertId: string) => void;
  onPatientClick?: (patientId: number) => void;
}

export default function AlertsModal({ isOpen, onClose, alerts, onAlertResolve, onPatientClick }: AlertsModalProps) {
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
      critical: 'border-red-600',
      high: 'border-red-500',
      medium: 'border-yellow-500',
      low: 'border-blue-500',
      info: 'border-neutral-300'
    };
    return colors[severity] || colors.info;
  };

  const activeAlerts = alerts.filter(a => a.status === 'active');

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="fixed top-20 right-6 w-[500px] max-h-[600px] bg-surface border border-neutral-200 rounded-lg shadow-2xl z-50 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="px-6 py-4 border-b-2 border-neutral-950 flex items-center justify-between flex-shrink-0">
              <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
                Active Alerts ({activeAlerts.length})
              </h2>
              <button
                onClick={onClose}
                className="text-neutral-500 hover:text-neutral-950 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {activeAlerts.length === 0 ? (
                <div className="flex items-center justify-center h-48">
                  <div className="text-center text-neutral-400">
                    <svg className="w-12 h-12 mx-auto mb-3 text-neutral-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm font-light">No active alerts</p>
                    <p className="text-xs font-light mt-1 text-neutral-400">All clear!</p>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-neutral-200">
                  {activeAlerts.map((alert, i) => (
                    <div
                      key={alert.id || i}
                      className={`border-l-4 ${getSeverityColor(alert.severity)} px-6 py-4 bg-white hover:bg-neutral-50 transition-all`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        {/* Left: Alert Info */}
                        <div 
                          className="flex-1 cursor-pointer"
                          onClick={() => {
                            if (alert.patient_id && onPatientClick) {
                              const patientNum = parseInt(alert.patient_id.replace(/\D/g, '')) || 0;
                              onPatientClick(patientNum);
                              onClose(); // Close modal after clicking
                            }
                          }}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${
                              alert.severity === 'critical' ? 'bg-red-600 text-white' :
                              alert.severity === 'high' ? 'bg-red-500 text-white' :
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
                            className="flex-shrink-0 px-3 py-1.5 text-xs font-medium text-white rounded transition-all"
                            style={{ backgroundColor: '#6B9080', borderColor: '#6B9080' }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#5a7a6d'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6B9080'}
                          >
                            Solved
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

