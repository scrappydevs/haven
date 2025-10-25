'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface Alert {
  patient_id: number;
  timestamp: string;
  message: string;
  crs_score: number;
  heart_rate: number;
  severity?: string;
}

interface AlertPanelProps {
  alerts: Alert[];
}

export default function AlertPanel({ alerts }: AlertPanelProps) {
  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 p-4 h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white">Live Alerts</h2>
        <div className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-semibold">
          {alerts.length} Active
        </div>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-250px)] overflow-y-auto">
        <AnimatePresence>
          {alerts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <div className="text-6xl mb-4">✅</div>
              <p className="text-slate-400 text-sm">No active alerts</p>
              <p className="text-slate-500 text-xs mt-2">All patients stable</p>
            </motion.div>
          ) : (
            alerts.map((alert, idx) => (
              <motion.div
                key={`${alert.patient_id}-${alert.timestamp}`}
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-red-500/10 border border-red-500/30 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-xl">🚨</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-semibold text-sm truncate">
                      {alert.message}
                    </p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-300">
                      <span>CRS: {(alert.crs_score * 100).toFixed(0)}%</span>
                      <span>•</span>
                      <span>HR: {alert.heart_rate} bpm</span>
                    </div>
                    <p className="text-slate-400 text-xs mt-2">
                      {new Date().toLocaleTimeString()}
                    </p>
                  </div>
                </div>

                <div className="mt-3 flex gap-2">
                  <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-xs py-2 rounded-lg font-semibold transition-colors">
                    Dispatch Nurse
                  </button>
                  <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs py-2 rounded-lg font-semibold transition-colors">
                    View Details
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

