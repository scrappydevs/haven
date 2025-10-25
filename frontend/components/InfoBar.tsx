'use client';

import { motion } from 'framer-motion';

interface InfoBarProps {
  patientId: string | number;
  patientName: string;
  heartRate?: number;
  crsScore?: number;
  isLive?: boolean;
  isSelected?: boolean;
  onClick?: () => void;
  monitoringLevel?: 'BASELINE' | 'ENHANCED' | 'CRITICAL';
}

export default function InfoBar({
  patientId,
  patientName,
  heartRate,
  crsScore,
  isLive = false,
  isSelected = false,
  onClick,
  monitoringLevel = 'BASELINE'
}: InfoBarProps) {

  // Determine border color based on CRS score
  const getBorderColor = () => {
    if (!crsScore) return 'border-neutral-300';
    if (crsScore > 0.7) return 'border-accent-terra';
    if (crsScore > 0.4) return 'border-primary-400';
    return 'border-primary-700';
  };

  const borderColor = getBorderColor();

  // Get monitoring level badge styling
  const getMonitoringBadgeStyle = () => {
    switch (monitoringLevel) {
      case 'CRITICAL':
        return {
          bg: 'bg-accent-terra/10',
          text: 'text-accent-terra',
          border: 'border-accent-terra',
          icon: '🚨'
        };
      case 'ENHANCED':
        return {
          bg: 'bg-primary-400/10',
          text: 'text-primary-400',
          border: 'border-primary-400',
          icon: '⚡'
        };
      default:  // BASELINE
        return {
          bg: 'bg-primary-700/10',
          text: 'text-primary-700',
          border: 'border-primary-700',
          icon: '📊'
        };
    }
  };

  const badgeStyle = getMonitoringBadgeStyle();

  return (
    <motion.div
      onClick={onClick}
      className={`
        px-4 py-2.5 cursor-pointer transition-all
        border-l-4 border border-neutral-200 bg-surface
        ${isSelected ? 'border-l-primary-950' : borderColor}
        hover:bg-neutral-50
      `}
      whileHover={{ x: 2 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-center justify-between gap-3">
        {/* Left: Patient Info */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="label-uppercase text-neutral-950">
            {isLive ? 'LIVE' : `P${patientId}`}
          </span>
          <span className="text-sm font-light text-neutral-700 truncate hidden sm:inline">
            {patientName}
          </span>
        </div>

        {/* Right: Vitals & Status */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {/* Heart Rate */}
          {heartRate !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="label-uppercase text-neutral-500">HR</span>
              <span className="text-sm font-light text-neutral-950">{heartRate}</span>
            </div>
          )}

          {/* CRS Score */}
          {crsScore !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="label-uppercase text-neutral-500">CRS</span>
              <span className={`text-sm font-normal ${
                crsScore > 0.7 ? 'text-accent-terra' :
                crsScore > 0.4 ? 'text-primary-400' :
                'text-primary-700'
              }`}>
                {(crsScore * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Monitoring Level Badge */}
          <div className={`
            flex items-center gap-1 px-2 py-0.5
            border ${badgeStyle.border} ${badgeStyle.bg}
            ${monitoringLevel !== 'BASELINE' ? 'animate-pulse' : ''}
          `}>
            <span className="text-xs">{badgeStyle.icon}</span>
            <span className={`label-uppercase text-[10px] ${badgeStyle.text}`}>
              {monitoringLevel}
            </span>
          </div>

          {/* Status Indicator */}
          {isLive && (
            <motion.div
              className="w-2 h-2 bg-primary-700"
              animate={{
                opacity: [1, 0.3, 1]
              }}
              transition={{
                repeat: Infinity,
                duration: 2
              }}
            />
          )}
        </div>
      </div>
    </motion.div>
  );
}
