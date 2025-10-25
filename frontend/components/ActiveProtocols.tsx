'use client';

import { motion } from 'framer-motion';

interface ActiveProtocolsProps {
  monitoringLevel: 'BASELINE' | 'ENHANCED' | 'CRITICAL';
  enabledMetrics: string[];
  timeRemaining?: string | null;
}

export default function ActiveProtocols({
  monitoringLevel,
  enabledMetrics,
  timeRemaining
}: ActiveProtocolsProps) {
  // Metric display names and descriptions
  const metricInfo: Record<string, { name: string; icon: string; category: string }> = {
    heart_rate: { name: 'Heart Rate (rPPG)', icon: '❤️', category: 'BASELINE' },
    respiratory_rate: { name: 'Respiratory Rate', icon: '💨', category: 'BASELINE' },
    crs_score: { name: 'CRS Facial Flushing', icon: '🌡️', category: 'BASELINE' },
    tremor_magnitude: { name: 'Tremor Detection (FFT)', icon: '📊', category: 'ENHANCED' },
    tremor_detected: { name: 'Tremor Alert System', icon: '⚠️', category: 'ENHANCED' },
    attention_score: { name: 'Attention Tracking', icon: '👁️', category: 'ENHANCED' },
    eye_openness: { name: 'Eye Openness Monitor', icon: '👀', category: 'ENHANCED' },
    face_touching_frequency: { name: 'Face Touching Monitor', icon: '✋', category: 'ENHANCED' },
    restlessness_index: { name: 'Restlessness Index', icon: '🔄', category: 'CRITICAL' },
    movement_vigor: { name: 'Movement Vigor Analysis', icon: '💪', category: 'CRITICAL' },
    head_pitch: { name: 'Head Pitch Tracking', icon: '↕️', category: 'CRITICAL' },
    head_yaw: { name: 'Head Yaw Tracking', icon: '↔️', category: 'CRITICAL' },
    head_roll: { name: 'Head Roll Tracking', icon: '🔄', category: 'CRITICAL' },
    posture_score: { name: 'Posture Analysis', icon: '🧍', category: 'CRITICAL' }
  };

  // Group metrics by category
  const baseline = enabledMetrics.filter(m => metricInfo[m]?.category === 'BASELINE');
  const enhanced = enabledMetrics.filter(m => metricInfo[m]?.category === 'ENHANCED');
  const critical = enabledMetrics.filter(m => metricInfo[m]?.category === 'CRITICAL');

  const getLevelStyle = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-accent-terra border-accent-terra bg-accent-terra/5';
      case 'ENHANCED':
        return 'text-primary-400 border-primary-400 bg-primary-400/5';
      default:
        return 'text-primary-700 border-primary-700 bg-primary-700/5';
    }
  };

  return (
    <div className="bg-surface border border-neutral-200">
      {/* Header */}
      <div className="border-b border-neutral-200 px-4 py-3">
        <h3 className="label-uppercase text-neutral-950 text-sm">
          Active Monitoring Protocols
        </h3>
        <p className="text-xs font-light text-neutral-500 mt-1">
          {enabledMetrics.length} metrics enabled
        </p>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* BASELINE - Always On */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className={`label-uppercase text-[10px] px-2 py-1 border ${getLevelStyle('BASELINE')}`}>
              📊 BASELINE
            </span>
            <span className="text-xs font-light text-neutral-500">Always Active</span>
          </div>
          <div className="space-y-1 ml-3">
            {baseline.map((metric) => (
              <motion.div
                key={metric}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-2 text-sm"
              >
                <span className="text-primary-700">✓</span>
                <span className="font-light text-neutral-700">
                  {metricInfo[metric]?.icon} {metricInfo[metric]?.name || metric}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* ENHANCED - If active */}
        {enhanced.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <motion.span
                animate={{ opacity: [1, 0.6, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className={`label-uppercase text-[10px] px-2 py-1 border ${getLevelStyle('ENHANCED')}`}
              >
                ⚡ ENHANCED
              </motion.span>
              {timeRemaining && monitoringLevel === 'ENHANCED' && (
                <span className="text-xs font-light text-primary-400">
                  {timeRemaining} remaining
                </span>
              )}
            </div>
            <div className="space-y-1 ml-3">
              {enhanced.map((metric, idx) => (
                <motion.div
                  key={metric}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <motion.span
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 2, delay: idx * 0.2 }}
                    className="text-primary-400"
                  >
                    ⚡
                  </motion.span>
                  <span className="font-light text-neutral-700">
                    {metricInfo[metric]?.icon} {metricInfo[metric]?.name || metric}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* CRITICAL - If active */}
        {critical.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
                className={`label-uppercase text-[10px] px-2 py-1 border ${getLevelStyle('CRITICAL')}`}
              >
                🚨 CRITICAL
              </motion.span>
              <span className="text-xs font-light text-accent-terra">
                High-Frequency Sampling
              </span>
            </div>
            <div className="space-y-1 ml-3">
              {critical.map((metric, idx) => (
                <motion.div
                  key={metric}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <motion.span
                    animate={{ scale: [1, 1.3, 1] }}
                    transition={{ repeat: Infinity, duration: 1, delay: idx * 0.1 }}
                    className="text-accent-terra"
                  >
                    🚨
                  </motion.span>
                  <span className="font-light text-neutral-700">
                    {metricInfo[metric]?.icon} {metricInfo[metric]?.name || metric}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Info box */}
        <div className="mt-4 pt-4 border-t border-neutral-200">
          <p className="text-xs font-light text-neutral-500">
            💡 Agent dynamically adjusts monitoring based on patient condition and clinical significance.
          </p>
        </div>
      </div>
    </div>
  );
}
