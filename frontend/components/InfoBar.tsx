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
}

export default function InfoBar({
  patientId,
  patientName,
  heartRate,
  crsScore,
  isLive = false,
  isSelected = false,
  onClick
}: InfoBarProps) {

  // Determine status color based on CRS score
  const getStatusColor = () => {
    if (!crsScore) return 'bg-slate-500';
    if (crsScore > 0.7) return 'bg-red-500';
    if (crsScore > 0.4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const statusColor = getStatusColor();

  return (
    <motion.div
      onClick={onClick}
      className={`
        px-3 py-2 cursor-pointer transition-all duration-200
        border-t-2 font-mono text-xs
        ${isSelected
          ? 'bg-blue-900/50 border-blue-500 shadow-lg shadow-blue-500/30'
          : 'bg-slate-900/80 border-slate-700 hover:bg-slate-800/80'
        }
      `}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="flex items-center justify-between gap-2">
        {/* Left: Patient Info */}
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-white font-semibold truncate">
            {isLive ? '🔴 LIVE' : `P${patientId}`}
          </span>
          <span className="text-slate-400 truncate hidden sm:inline">
            {patientName}
          </span>
        </div>

        {/* Right: Vitals & Status */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Heart Rate */}
          {heartRate !== undefined && (
            <div className="flex items-center gap-1">
              <span className="text-slate-400">HR:</span>
              <span className="text-white font-semibold">{heartRate}</span>
            </div>
          )}

          {/* CRS Score */}
          {crsScore !== undefined && (
            <div className="flex items-center gap-1">
              <span className="text-slate-400">CRS:</span>
              <span className={`font-semibold ${
                crsScore > 0.7 ? 'text-red-400' :
                crsScore > 0.4 ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {(crsScore * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Status Indicator */}
          <div className="flex items-center gap-1">
            <motion.div
              className={`w-2 h-2 rounded-full ${statusColor}`}
              animate={{
                scale: isLive ? [1, 1.2, 1] : 1,
                opacity: isLive ? [1, 0.7, 1] : 1
              }}
              transition={{
                repeat: isLive ? Infinity : 0,
                duration: 1.5
              }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
