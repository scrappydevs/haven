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
    confidence?: number;
    concerns?: string[];
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

    // Map event types to terminal log types
    let terminalType: 'vital' | 'agent_thinking' | 'agent_action' | 'agent_reasoning' | 'monitoring' | 'alert' = 'monitoring';

    if (latestEvent.type === 'agent_thinking') terminalType = 'agent_thinking';
    else if (latestEvent.type === 'agent_reasoning') terminalType = 'agent_reasoning';
    else if (latestEvent.type === 'agent_action') terminalType = 'agent_action';
    else if (latestEvent.type === 'alert') terminalType = 'alert';
    else if (latestEvent.type === 'vital') terminalType = 'vital';
    else if (latestEvent.type === 'monitoring') terminalType = 'monitoring';

    const newEntry: TerminalLogEntry = {
      id: logIdCounter,
      timestamp: new Date(latestEvent.timestamp),
      type: terminalType,
      severity: latestEvent.severity === 'high' || latestEvent.severity === 'critical' ? 'critical' :
                latestEvent.severity === 'moderate' || latestEvent.severity === 'warning' ? 'warning' : 'normal',
      message: latestEvent.message,
      details: latestEvent.details,
      highlight: terminalType.startsWith('agent_') || terminalType === 'alert',
      metadata: {
        confidence: latestEvent.confidence,
        concerns: latestEvent.concerns
      }
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

    // Only log significant changes (throttle) - but always log concerning values
    const hrConcerning = hr > 90;
    const rrConcerning = rr > 18;
    const crsConcerning = crs > 0.5;
    const shouldLog = hrConcerning || rrConcerning || crsConcerning || Math.random() < 0.15; // 15% chance + always log concerning

    if (!shouldLog) return;

    // Log HR if concerning or random
    if (hr && (hrConcerning || Math.random() < 0.3)) {
      const status = hr > 100 ? '⚠️ [ELEVATED]' : hr > 90 ? '↑ [HIGH]' : '✓ [NORMAL]';
      const entry: TerminalLogEntry = {
        id: logIdCounter,
        timestamp: new Date(),
        type: 'vital',
        severity: hr > 100 ? 'critical' : hr > 90 ? 'warning' : 'normal',
        message: `HR  → ${hr} bpm ${status}`,
        metadata: { value: hr }
      };
      setTerminalEntries(prev => [...prev, entry].slice(-100)); // Keep last 100
      setLogIdCounter(prev => prev + 1);
    }

    // Log RR if concerning
    if (rr && (rrConcerning || Math.random() < 0.3)) {
      const status = rr > 22 ? '⚠️ [ELEVATED]' : rr > 18 ? '↑ [HIGH]' : '✓ [NORMAL]';
      const entry: TerminalLogEntry = {
        id: logIdCounter + 1,
        timestamp: new Date(),
        type: 'vital',
        severity: rr > 22 ? 'critical' : rr > 18 ? 'warning' : 'normal',
        message: `RR  → ${rr} /min ${status}`,
        metadata: { value: rr }
      };
      setTerminalEntries(prev => [...prev, entry].slice(-100));
      setLogIdCounter(prev => prev + 1);
    }

    // Log CRS if concerning
    if (crs !== undefined && (crsConcerning || Math.random() < 0.3)) {
      const status = crs > 0.7 ? '🚨 [CRITICAL]' : crs > 0.5 ? '⚠️ [CONCERNING]' : '✓ [STABLE]';
      const entry: TerminalLogEntry = {
        id: logIdCounter + 2,
        timestamp: new Date(),
        type: 'vital',
        severity: crs > 0.7 ? 'critical' : crs > 0.5 ? 'warning' : 'normal',
        message: `CRS → ${crs.toFixed(2)} ${status}`,
        metadata: { value: crs }
      };
      setTerminalEntries(prev => [...prev, entry].slice(-100));
      setLogIdCounter(prev => prev + 1);
    }
  }, [cvData?.metrics?.heart_rate, cvData?.metrics?.respiratory_rate, cvData?.metrics?.crs_score]);

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

  // Calculate time remaining for display
  const timeRemaining = monitoringExpiresAt ? calculateTimeRemaining(monitoringExpiresAt) : null;

  // Get monitoring level badge styling
  const getMonitoringBadge = () => {
    const baseClasses = "px-2 py-0.5 text-xs font-semibold border transition-all duration-300";

    if (monitoringLevel === 'CRITICAL') {
      return {
        className: `${baseClasses} border-red-600 bg-red-600/20 text-red-600 shadow-lg shadow-red-500/50`,
        icon: '🚨',
        label: 'CRITICAL'
      };
    } else if (monitoringLevel === 'ENHANCED') {
      return {
        className: `${baseClasses} border-yellow-600 bg-yellow-600/20 text-yellow-600 shadow-lg shadow-yellow-500/30`,
        icon: '⚡',
        label: 'ENHANCED'
      };
    } else {
      return {
        className: `${baseClasses} border-neutral-400 bg-neutral-100 text-neutral-600`,
        icon: '📊',
        label: 'BASELINE'
      };
    }
  };

  const badge = getMonitoringBadge();

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-surface border border-neutral-200 overflow-hidden h-full flex flex-col"
    >
      {/* ========== COMPACT PATIENT HEADER ========== */}
      <div className="border-b border-neutral-200 bg-neutral-50 px-3 py-1.5 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-light text-neutral-950">
              {patient.name}
            </h3>
            <span className="text-xs text-neutral-500">• {patient.age}y/o</span>
            {patient.condition && (
              <span className="text-xs text-neutral-500">• {patient.condition}</span>
            )}
          </div>
          <div className={`px-2 py-0.5 text-xs font-semibold border ${
            alert ? 'border-accent-terra bg-accent-terra/10 text-accent-terra' :
                   'border-green-600 bg-green-600/10 text-green-600'
          }`}>
            {alert ? '⚠️ Alert' : '✓ Stable'}
          </div>
        </div>
      </div>

      {/* ========== COMPACT AGENT STATUS LINE ========== */}
      <div className="border-b border-neutral-200 bg-neutral-900 px-3 py-1.5 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isAgentAnalyzing ? (
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="text-sm text-cyan-400 font-mono"
              >
                🤖 Analyzing...
              </motion.span>
            ) : (
              <span className="text-sm text-green-400 font-mono flex items-center gap-2">
                👁️ Watching
              </span>
            )}
            <span className="text-neutral-600">│</span>
            <motion.div
              className={badge.className}
              animate={isAgentAnalyzing ? { scale: [1, 1.05, 1] } : {}}
              transition={{ repeat: isAgentAnalyzing ? Infinity : 0, duration: 2 }}
            >
              {badge.icon} {badge.label}
            </motion.div>
            {timeRemaining && monitoringLevel !== 'BASELINE' && (
              <>
                <span className="text-neutral-600">│</span>
                <span className="text-xs text-neutral-400 font-mono">⏱️ {timeRemaining}</span>
              </>
            )}
          </div>
          <div className="text-xs text-neutral-500 font-mono">
            {agentStats.decisionsToday} decisions
          </div>
        </div>
      </div>

      {/* ========== TERMINAL LOG (MAIN FEATURE - 80% OF SPACE) ========== */}
      <div className="flex-1 overflow-hidden">
        <TerminalLog entries={terminalEntries} maxHeight="100%" />
      </div>

      {/* ========== MINIMAL FOOTER WITH QUICK VITALS ========== */}
      <div className="border-t border-neutral-200 bg-neutral-900 px-3 py-1.5 flex-shrink-0">
        <div className="flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-3 text-neutral-400">
            <span className={heartRate > 100 ? 'text-red-400' : heartRate > 90 ? 'text-yellow-400' : 'text-green-400'}>
              ❤️ {heartRate ?? '--'}
            </span>
            <span className="text-neutral-600">│</span>
            <span className={respiratoryRate > 22 ? 'text-red-400' : respiratoryRate > 18 ? 'text-yellow-400' : 'text-green-400'}>
              💨 {respiratoryRate ?? '--'}
            </span>
            <span className="text-neutral-600">│</span>
            <span className={crsScore > 0.7 ? 'text-red-400' : crsScore > 0.4 ? 'text-yellow-400' : 'text-green-400'}>
              🌡️ {crsScore ? `${(crsScore * 100).toFixed(0)}%` : '--'}
            </span>
            <span className="text-neutral-600">│</span>
            <span className="text-neutral-500">
              👁️ {enabledMetrics.length} metrics
            </span>
          </div>
          <span className="text-neutral-500 text-xs">
            AI: Claude 3.5 Sonnet
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
