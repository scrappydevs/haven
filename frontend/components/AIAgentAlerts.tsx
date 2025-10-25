'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { API_URL } from '@/lib/api-config';

interface AgentAlert {
  patient_id: string;
  severity: string;
  message: string;
  concerns: string[];
  confidence: number;
  actions: string[];
  timestamp: string;
  metrics?: {
    heart_rate?: number;
    respiratory_rate?: number;
    crs_score?: number;
    tremor_detected?: boolean;
  };
}

interface AIAgentAlertsProps {
  className?: string;
}

export default function AIAgentAlerts({ className = '' }: AIAgentAlertsProps) {
  const [alerts, setAlerts] = useState<AgentAlert[]>([]);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    // Fetch initial status
    fetchSystemStatus();
    fetchAlerts();

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      fetchAlerts();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/agents/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch agent status:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_URL}/agents/alerts`);
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to fetch agent alerts:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'border-red-500 bg-red-50';
      case 'CONCERNING':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-blue-500 bg-blue-50';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return '🚨';
      case 'CONCERNING':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className={`bg-surface border border-neutral-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b-2 border-neutral-950">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-normal uppercase tracking-wider text-neutral-950">
              🤖 AI AGENT ALERTS
            </h2>
            <p className="text-xs font-light text-neutral-500 mt-1">
              Fetch.ai + Anthropic Claude
            </p>
          </div>
          <div className="flex items-center gap-3">
            {systemStatus?.enabled ? (
              <div className="flex items-center gap-2 px-3 py-1.5 border border-green-500 bg-green-50 rounded">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium text-green-700">ACTIVE</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 bg-gray-50 rounded">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <span className="text-xs font-medium text-gray-600">OFFLINE</span>
              </div>
            )}
            <div className="px-3 py-1.5 border border-accent-terra bg-accent-terra/5 rounded">
              <span className="text-accent-terra text-xs font-medium">{alerts.length} Alerts</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto">
        <AnimatePresence>
          {!systemStatus?.enabled ? (
            <div className="text-center py-12 border border-neutral-200 bg-neutral-50 rounded">
              <p className="text-neutral-600 text-sm font-light mb-2">
                AI Agent System Offline
              </p>
              <p className="text-xs font-light text-neutral-500">
                Install uagents: pip install uagents&gt;=0.12.0
              </p>
            </div>
          ) : alerts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 border border-neutral-200 bg-neutral-50 rounded"
            >
              <p className="text-primary-700 text-base font-light mb-2">All Patients Stable</p>
              <p className="text-neutral-500 text-xs font-light">
                AI agents monitoring continuously
              </p>
            </motion.div>
          ) : (
            alerts.map((alert, idx) => (
              <motion.div
                key={`${alert.patient_id}-${alert.timestamp}`}
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -50, opacity: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`border-l-4 border rounded p-5 ${getSeverityColor(alert.severity)}`}
              >
                {/* Alert Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getSeverityIcon(alert.severity)}</span>
                    <div>
                      <h3 className="font-medium text-sm text-neutral-950">
                        Patient {alert.patient_id}
                      </h3>
                      <span className={`text-xs font-medium ${
                        alert.severity === 'CRITICAL' ? 'text-red-700' :
                        alert.severity === 'CONCERNING' ? 'text-yellow-700' :
                        'text-blue-700'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-light text-neutral-500">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="text-xs font-medium text-neutral-700 mt-1">
                      AI Confidence: {(alert.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* AI Reasoning */}
                <div className="mb-3 p-3 bg-white/50 rounded border border-neutral-200">
                  <p className="text-xs font-medium text-neutral-600 mb-1">AI REASONING:</p>
                  <p className="text-sm font-light text-neutral-800">{alert.message}</p>
                </div>

                {/* Vitals */}
                {alert.metrics && (
                  <div className="flex gap-4 mb-3 text-xs font-light text-neutral-600">
                    {alert.metrics.heart_rate && (
                      <span>HR: {alert.metrics.heart_rate} bpm</span>
                    )}
                    {alert.metrics.respiratory_rate && (
                      <span>RR: {alert.metrics.respiratory_rate}/min</span>
                    )}
                    {alert.metrics.crs_score !== undefined && (
                      <span>CRS: {(alert.metrics.crs_score * 100).toFixed(0)}%</span>
                    )}
                    {alert.metrics.tremor_detected && (
                      <span className="text-red-600">⚠️ Tremor Detected</span>
                    )}
                  </div>
                )}

                {/* Concerns */}
                {alert.concerns && alert.concerns.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-neutral-600 mb-1">CONCERNS:</p>
                    <div className="flex flex-wrap gap-2">
                      {alert.concerns.map((concern, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-white border border-neutral-300 rounded text-xs font-light text-neutral-700"
                        >
                          {concern}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Actions */}
                {alert.actions && alert.actions.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-neutral-600 mb-2">RECOMMENDED ACTIONS:</p>
                    <ul className="space-y-1">
                      {alert.actions.map((action, i) => (
                        <li key={i} className="text-xs font-light text-neutral-700 flex items-start gap-2">
                          <span className="text-neutral-400">•</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Footer - System Info */}
      {systemStatus && systemStatus.enabled && (
        <div className="px-6 py-3 border-t border-neutral-200 bg-neutral-50">
          <div className="flex items-center justify-between text-xs font-light text-neutral-600">
            <div>
              Patients Monitored: <span className="font-medium">{systemStatus.patients_monitored || 0}</span>
            </div>
            <div>
              Total Events: <span className="font-medium">{systemStatus.total_events || 0}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-green-500">●</span>
              <span>Claude AI Active</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

