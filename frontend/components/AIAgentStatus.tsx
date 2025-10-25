'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface LastDecision {
  timestamp: Date;
  action: string;
  reason: string;
  confidence: number;
}

interface AIAgentStatusProps {
  isActive: boolean;
  isAnalyzing?: boolean;
  monitoringLevel: 'BASELINE' | 'ENHANCED' | 'CRITICAL';
  expiresAt?: string | null;
  lastDecision?: LastDecision | null;
  decisionsToday?: number;
  escalationsToday?: number;
}

export default function AIAgentStatus({
  isActive,
  isAnalyzing = false,
  monitoringLevel,
  expiresAt,
  lastDecision,
  decisionsToday = 0,
  escalationsToday = 0
}: AIAgentStatusProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  // Calculate time remaining for enhanced/critical monitoring
  useEffect(() => {
    if (!expiresAt) {
      setTimeRemaining('');
      return;
    }

    const updateTimer = () => {
      const now = new Date();
      const expiry = new Date(expiresAt);
      const diff = expiry.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining('Expired');
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  const getMonitoringStyle = () => {
    switch (monitoringLevel) {
      case 'CRITICAL':
        return {
          bg: 'bg-accent-terra/10',
          border: 'border-accent-terra',
          text: 'text-accent-terra',
          glow: 'shadow-lg shadow-accent-terra/20',
          icon: '🚨'
        };
      case 'ENHANCED':
        return {
          bg: 'bg-primary-400/10',
          border: 'border-primary-400',
          text: 'text-primary-400',
          glow: 'shadow-lg shadow-primary-400/20',
          icon: '⚡'
        };
      default:
        return {
          bg: 'bg-primary-700/10',
          border: 'border-primary-700',
          text: 'text-primary-700',
          glow: '',
          icon: '📊'
        };
    }
  };

  const style = getMonitoringStyle();

  const getTimeSince = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div className="space-y-4">
      {/* Agent Active Indicator */}
      <div className="bg-surface border border-neutral-200 p-4">
        <div className="flex items-center gap-3">
          {isAnalyzing ? (
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 1 }}
              className="text-2xl"
            >
              🤖
            </motion.div>
          ) : (
            <motion.div
              animate={{ opacity: isActive ? [1, 0.5, 1] : 1 }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="text-2xl"
            >
              👁️
            </motion.div>
          )}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-light text-neutral-950">
                {isAnalyzing ? 'AI Agent Analyzing...' : 'AI Agent Watching'}
              </h3>
              {isActive && (
                <motion.div
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  className="w-2 h-2 bg-green-500 rounded-full"
                />
              )}
            </div>
            <p className="label-uppercase text-neutral-500 text-[10px] mt-0.5">
              Fetch.ai Health Agent • Claude 3.5 Sonnet
            </p>
          </div>
        </div>
      </div>

      {/* Monitoring Level - Large & Prominent */}
      <div className={`${style.bg} ${style.border} border-2 p-6 ${style.glow} transition-all`}>
        <div className="text-center">
          <p className="label-uppercase text-neutral-500 text-xs mb-2">
            Current Monitoring Level
          </p>
          <motion.div
            animate={monitoringLevel !== 'BASELINE' ? { scale: [1, 1.05, 1] } : {}}
            transition={{ repeat: Infinity, duration: 2 }}
            className="flex items-center justify-center gap-3 mb-2"
          >
            <span className="text-4xl">{style.icon}</span>
            <h2 className={`text-3xl font-light tracking-wider ${style.text}`}>
              {monitoringLevel}
            </h2>
          </motion.div>
          {timeRemaining && (
            <div className={`${style.text} text-sm font-light mt-2`}>
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
              >
                Expires in: {timeRemaining}
              </motion.span>
            </div>
          )}
        </div>
      </div>

      {/* Last Decision */}
      {lastDecision && (
        <div className="bg-neutral-50 border border-neutral-200 p-4">
          <div className="flex items-start justify-between gap-2 mb-3">
            <h3 className="label-uppercase text-neutral-700">Last Decision</h3>
            <span className="text-xs font-light text-neutral-500">
              {getTimeSince(lastDecision.timestamp)}
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <span className="label-uppercase text-neutral-500 text-[10px]">Action</span>
              <p className="text-sm font-light text-neutral-950 mt-0.5">
                {lastDecision.action}
              </p>
            </div>

            <div>
              <span className="label-uppercase text-neutral-500 text-[10px]">Reasoning</span>
              <p className="text-sm font-light text-neutral-700 mt-0.5">
                "{lastDecision.reason}"
              </p>
            </div>

            {/* Confidence Bar */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="label-uppercase text-neutral-500 text-[10px]">
                  Confidence
                </span>
                <span className={`text-xs font-semibold ${
                  lastDecision.confidence > 0.8 ? 'text-green-600' :
                  lastDecision.confidence > 0.6 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {(lastDecision.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-neutral-200 h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${lastDecision.confidence * 100}%` }}
                  transition={{ duration: 0.5 }}
                  className={`h-full ${
                    lastDecision.confidence > 0.8 ? 'bg-green-600' :
                    lastDecision.confidence > 0.6 ? 'bg-yellow-600' :
                    'bg-red-600'
                  }`}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Decision Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface border border-neutral-200 p-3 text-center">
          <p className="text-2xl font-light text-neutral-950">{decisionsToday}</p>
          <p className="label-uppercase text-neutral-500 text-[10px] mt-1">
            Decisions Today
          </p>
        </div>
        <div className="bg-surface border border-neutral-200 p-3 text-center">
          <p className="text-2xl font-light text-accent-terra">{escalationsToday}</p>
          <p className="label-uppercase text-neutral-500 text-[10px] mt-1">
            Escalations
          </p>
        </div>
      </div>
    </div>
  );
}
