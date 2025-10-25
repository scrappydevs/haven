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
    <div className="bg-surface border border-neutral-200 p-8 h-full">
      <div className="flex items-center justify-between mb-8 border-b-2 border-neutral-950 pb-4">
        <h2 className="text-2xl font-light tracking-tight text-neutral-950">LIVE ALERTS</h2>
        <div className="px-4 py-1.5 border border-accent-terra bg-accent-terra/5">
          <span className="label-uppercase text-accent-terra">{alerts.length} Active</span>
        </div>
      </div>

      <div className="space-y-4 max-h-[calc(100vh-250px)] overflow-y-auto">
        <AnimatePresence>
          {alerts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16 border border-neutral-200 bg-neutral-50"
            >
              <p className="text-primary-700 text-xl font-light mb-2">All Systems Nominal</p>
              <p className="text-neutral-500 text-sm font-light">No active alerts at this time</p>
            </motion.div>
          ) : (
            alerts.map((alert, idx) => (
              <motion.div
                key={`${alert.patient_id}-${alert.timestamp}`}
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -50, opacity: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="border-l-4 border-accent-terra border border-neutral-200 bg-surface p-6"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <p className="text-neutral-950 font-light text-base mb-2">
                      {alert.message}
                    </p>
                    <div className="flex items-center gap-6 text-xs text-neutral-500 font-light">
                      <span className="label-uppercase">CRS: {(alert.crs_score * 100).toFixed(0)}%</span>
                      <span>•</span>
                      <span className="label-uppercase">HR: {alert.heart_rate} BPM</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex gap-3">
                  <button className="border-2 border-neutral-950 px-6 py-2 font-normal text-xs uppercase tracking-widest hover:bg-neutral-950 hover:text-white transition-all">
                    Dispatch Nurse
                  </button>
                  <button className="border border-neutral-300 px-6 py-2 font-light text-xs uppercase tracking-wider text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 transition-colors">
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

