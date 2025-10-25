'use client';

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import AIAgentStatus from './AIAgentStatus';
import TerminalLog, { TerminalLogEntry } from './TerminalLog';
import ActiveProtocols from './ActiveProtocols';

interface DetailPanelProps {
  patient: {
    id: number;
    name: string;
    age?: number;
    condition?: string;
  } | null;
  cvData: {
    metrics?: {
      heart_rate?: number;
      respiratory_rate?: number;
      crs_score?: number;
      face_touching_frequency?: number;
      restlessness_index?: number;
      tremor_magnitude?: number;
      tremor_detected?: boolean;
      movement_vigor?: number;
      alert?: boolean;
      alert_triggers?: string[];
      head_pitch?: number;
      head_yaw?: number;
      head_roll?: number;
      attention_score?: number;
      eye_openness?: number;
    };
    heart_rate?: number;
    respiratory_rate?: number;
    crs_score?: number;
    alert?: boolean;
    alert_triggers?: string[];
  } | null;
  isLive?: boolean;
  monitoringConditions?: string[];
  events?: Array<{
    timestamp: string;
    type: string;
    severity: string;
    message: string;
    details: string;
  }>;
  monitoringLevel?: 'BASELINE' | 'ENHANCED' | 'CRITICAL';
  monitoringExpiresAt?: string | null;
  enabledMetrics?: string[];
  isAgentAnalyzing?: boolean;
  lastAgentDecision?: {
    timestamp: Date;
    action: string;
    reason: string;
    confidence: number;
  } | null;
  agentStats?: {
    decisionsToday: number;
    escalationsToday: number;
  };
}

export default function DetailPanel({
  patient,
  cvData,
  isLive = false,
  monitoringConditions = [],
  events = [],
  monitoringLevel = 'BASELINE',
  monitoringExpiresAt,
  enabledMetrics = ['heart_rate', 'respiratory_rate', 'crs_score'],
  isAgentAnalyzing = false,
  lastAgentDecision,
  agentStats = { decisionsToday: 0, escalationsToday: 0 }
}: DetailPanelProps) {
  const [terminalEntries, setTerminalEntries] = useState<TerminalLogEntry[]>([]);
  const [logIdCounter, setLogIdCounter] = useState(0);

  // Helper to get value from either nested metrics or flat structure
  const getValue = (key: string): any => {
    return cvData?.metrics?.[key as keyof typeof cvData.metrics] ?? cvData?.[key as keyof typeof cvData];
  };

  // Convert regular events to terminal log entries
  useEffect(() => {
    if (!events || events.length === 0) return;

    const latestEvent = events[0]; // Get most recent event
    const newEntry: TerminalLogEntry = {
      id: logIdCounter,
      timestamp: new Date(latestEvent.timestamp),
      type: latestEvent.type === 'agent' ? 'agent_action' :
            latestEvent.type === 'alert' ? 'alert' :
            latestEvent.type === 'vital' ? 'vital' : 'monitoring',
      severity: latestEvent.severity === 'high' ? 'critical' :
                latestEvent.severity === 'moderate' ? 'warning' : 'normal',
      message: latestEvent.message,
      details: latestEvent.details,
      highlight: latestEvent.type === 'agent' || latestEvent.type === 'alert'
    };

    setTerminalEntries(prev => [...prev, newEntry]);
    setLogIdCounter(prev => prev + 1);
  }, [events?.length]); // Only trigger when events array length changes

  // Add vital sign entries when metrics update
  useEffect(() => {
    if (!cvData?.metrics) return;

    const hr = getValue('heart_rate');
    const rr = getValue('respiratory_rate');
    const crs = getValue('crs_score');

    // Only log significant changes (throttle)
    const shouldLog = Math.random() < 0.2; // 20% chance to log (reduces spam)
    if (!shouldLog) return;

    if (hr) {
      const entry: TerminalLogEntry = {
        id: logIdCounter,
        timestamp: new Date(),
        type: 'vital',
        severity: hr > 100 ? 'critical' : hr > 90 ? 'warning' : 'normal',
        message: `HR → ${hr} bpm`,
        metadata: { value: hr }
      };
      setTerminalEntries(prev => [...prev, entry].slice(-100)); // Keep last 100
      setLogIdCounter(prev => prev + 1);
    }
  }, [cvData?.metrics?.heart_rate]);

  // Basic vitals
  const heartRate = getValue('heart_rate');
  const respiratoryRate = getValue('respiratory_rate');
  const alert = getValue('alert');
  const alertTriggers = getValue('alert_triggers') || [];
  const crsScore = getValue('crs_score');

  if (!patient) {
    return (
      <div className="bg-surface border border-neutral-200 p-8 h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-4">👁️</p>
          <p className="text-neutral-500 text-sm font-light">
            Select a patient to view AI monitoring
          </p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-surface border border-neutral-200 overflow-hidden h-full flex flex-col"
    >
      {/* ========== PATIENT HEADER ========== */}
      <div className="border-b-2 border-neutral-950 bg-neutral-50 px-6 py-4 flex-shrink-0">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-light text-neutral-950 mb-1">
              {patient.name}
            </h3>
            <div className="flex items-center gap-3 text-xs text-neutral-500">
              <span>Patient #{patient.id}</span>
              {patient.age && <span>• {patient.age}y/o</span>}
              {isLive && (
                <span className="flex items-center gap-1 text-primary-700">
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="w-2 h-2 bg-primary-700 rounded-full"
                  />
                  LIVE
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className={`px-3 py-1 text-xs font-semibold border ${
              alert ? 'border-accent-terra bg-accent-terra/10 text-accent-terra' :
                     'border-green-600 bg-green-600/10 text-green-600'
            }`}>
              {alert ? '⚠️ Alert' : '✓ Stable'}
            </div>
            {alert && alertTriggers.length > 0 && (
              <p className="text-xs text-accent-terra mt-1">
                {alertTriggers.join(' • ')}
              </p>
            )}
          </div>
        </div>
        {patient.condition && (
          <p className="text-sm font-light text-neutral-700 mt-2">
            {patient.condition}
          </p>
        )}
      </div>

      {/* ========== SCROLLABLE CONTENT ========== */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* ========== AI AGENT STATUS (PROMINENT) ========== */}
          <AIAgentStatus
            isActive={true}
            isAnalyzing={isAgentAnalyzing}
            monitoringLevel={monitoringLevel}
            expiresAt={monitoringExpiresAt}
            lastDecision={lastAgentDecision}
            decisionsToday={agentStats.decisionsToday}
            escalationsToday={agentStats.escalationsToday}
          />

          {/* ========== TERMINAL LOG (MAIN FEATURE) ========== */}
          <div>
            <h3 className="label-uppercase text-neutral-950 text-sm mb-3 flex items-center gap-2">
              <span>AI Agent Activity Log</span>
              <motion.div
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-2 h-2 bg-green-500 rounded-full"
              />
            </h3>
            <TerminalLog entries={terminalEntries} maxHeight="400px" />
          </div>

          {/* ========== ACTIVE PROTOCOLS ========== */}
          <ActiveProtocols
            monitoringLevel={monitoringLevel}
            enabledMetrics={enabledMetrics}
            timeRemaining={monitoringExpiresAt ? calculateTimeRemaining(monitoringExpiresAt) : null}
          />

          {/* ========== CURRENT VITALS SUMMARY ========== */}
          <div className="bg-neutral-50 border border-neutral-200 p-4">
            <h3 className="label-uppercase text-neutral-700 text-xs mb-3">
              Current Vitals Summary
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <p className="text-xs text-neutral-500 mb-1">Heart Rate</p>
                <p className={`text-2xl font-light ${
                  heartRate > 100 ? 'text-red-600' :
                  heartRate > 90 ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {heartRate ?? '--'}
                </p>
                <p className="text-xs text-neutral-400">bpm</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-neutral-500 mb-1">Resp. Rate</p>
                <p className={`text-2xl font-light ${
                  respiratoryRate > 22 ? 'text-red-600' :
                  respiratoryRate > 18 ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {respiratoryRate ?? '--'}
                </p>
                <p className="text-xs text-neutral-400">/min</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-neutral-500 mb-1">CRS Score</p>
                <p className={`text-2xl font-light ${
                  crsScore > 0.7 ? 'text-red-600' :
                  crsScore > 0.4 ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {crsScore ? `${(crsScore * 100).toFixed(0)}%` : '--'}
                </p>
                <p className="text-xs text-neutral-400">risk</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ========== FOOTER ========== */}
      <div className="border-t border-neutral-200 bg-neutral-50 px-6 py-3 flex-shrink-0">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ scale: [1, 1.5, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="w-2 h-2 bg-green-500 rounded-full"
            />
            <span className="text-neutral-700 font-light">
              AI Agent Active • Claude 3.5 Sonnet
            </span>
          </div>
          <span className="text-neutral-500">
            {terminalEntries.length} log entries
          </span>
        </div>
      </div>
    </motion.div>
  );
}

// Helper function to calculate time remaining
function calculateTimeRemaining(expiresAt: string): string {
  const now = new Date();
  const expiry = new Date(expiresAt);
  const diff = expiry.getTime() - now.getTime();

  if (diff <= 0) return 'Expired';

  const minutes = Math.floor(diff / 60000);
  const seconds = Math.floor((diff % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}
