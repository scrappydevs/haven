'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface AgentAlert {
  id: number;
  patient_id: string;
  patientName: string;
  severity: 'INFO' | 'MONITORING' | 'CRITICAL';
  message: string;
  reasoning?: string;
  concerns?: string[];
  confidence?: number;
  actions?: string[];
}

interface AgentAlertToastProps {
  alerts: AgentAlert[];
  onDismiss: (id: number) => void;
}

export default function AgentAlertToast({ alerts, onDismiss }: AgentAlertToastProps) {
  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return {
          bg: 'bg-accent-terra/10',
          border: 'border-accent-terra',
          text: 'text-accent-terra',
          icon: '🚨'
        };
      case 'MONITORING':
        return {
          bg: 'bg-primary-400/10',
          border: 'border-primary-400',
          text: 'text-primary-400',
          icon: '⚡'
        };
      default:  // INFO
        return {
          bg: 'bg-primary-700/10',
          border: 'border-primary-700',
          text: 'text-primary-700',
          icon: '✅'
        };
    }
  };

  return (
    <div className="fixed top-20 right-6 z-50 flex flex-col gap-3 max-w-md">
      <AnimatePresence>
        {alerts.map((alert) => {
          const style = getSeverityStyle(alert.severity);

          return (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: 100, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.8 }}
              transition={{ type: 'spring', damping: 20 }}
              className={`
                ${style.bg} ${style.border} border-2
                p-4 shadow-lg
                cursor-pointer
              `}
              onClick={() => onDismiss(alert.id)}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className="text-2xl flex-shrink-0 mt-0.5">
                  {style.icon}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h4 className={`font-semibold ${style.text} text-sm`}>
                        {alert.message}
                      </h4>
                      <p className="label-uppercase text-neutral-600 text-[10px] mt-0.5">
                        {alert.patientName} • {alert.patient_id}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDismiss(alert.id);
                      }}
                      className="text-neutral-400 hover:text-neutral-700 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>

                  {/* Reasoning */}
                  {alert.reasoning && (
                    <p className="text-xs text-neutral-700 mb-2 font-light">
                      {alert.reasoning}
                    </p>
                  )}

                  {/* Concerns */}
                  {alert.concerns && alert.concerns.length > 0 && (
                    <div className="mb-2">
                      <p className="label-uppercase text-neutral-500 text-[10px] mb-1">Concerns:</p>
                      <ul className="text-xs text-neutral-700 space-y-0.5">
                        {alert.concerns.map((concern, idx) => (
                          <li key={idx} className="flex items-start gap-1">
                            <span className="text-accent-terra">•</span>
                            <span>{concern}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Actions */}
                  {alert.actions && alert.actions.length > 0 && (
                    <div className="mb-2">
                      <p className="label-uppercase text-neutral-500 text-[10px] mb-1">Actions:</p>
                      <ul className="text-xs text-neutral-700 space-y-0.5">
                        {alert.actions.map((action, idx) => (
                          <li key={idx} className="flex items-start gap-1">
                            <span className={style.text}>→</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Confidence */}
                  {alert.confidence !== undefined && (
                    <div className="mt-2 pt-2 border-t border-neutral-200">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="label-uppercase text-neutral-500">AI Confidence</span>
                        <span className={`font-semibold ${style.text}`}>
                          {(alert.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-neutral-200 h-1 mt-1">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${alert.confidence * 100}%` }}
                          transition={{ duration: 0.5, delay: 0.2 }}
                          className={`h-full ${style.border === 'border-accent-terra' ? 'bg-accent-terra' : style.border === 'border-primary-400' ? 'bg-primary-400' : 'bg-primary-700'}`}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
