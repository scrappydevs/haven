'use client';

import { motion } from 'framer-motion';

interface DetailPanelProps {
  patient: {
    id: number;
    name: string;
    age?: number;
    condition?: string;
  } | null;
  cvData: {
    metrics?: {
      // Basic vitals (CV-derived)
      heart_rate?: number;
      respiratory_rate?: number;

      // CRS-specific
      crs_score?: number;
      face_touching_frequency?: number;
      restlessness_index?: number;

      // Seizure-specific
      tremor_magnitude?: number;
      tremor_detected?: boolean;
      movement_vigor?: number;

      // General
      alert?: boolean;
      head_pitch?: number;
      head_yaw?: number;
      head_roll?: number;
    };
    // Legacy flat format
    heart_rate?: number;
    respiratory_rate?: number;
    crs_score?: number;
    alert?: boolean;
  } | null;
  isLive?: boolean;
  monitoringConditions?: string[];  // NEW: Which conditions are being monitored
}

export default function DetailPanel({ patient, cvData, isLive = false, monitoringConditions = [] }: DetailPanelProps) {
  if (!patient) {
    return (
      <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-6">
        <p className="text-slate-400 text-center text-sm">
          Select a patient to view details
        </p>
      </div>
    );
  }

  // Helper to get value from either nested metrics or flat structure
  const getValue = (key: string): any => {
    return cvData?.metrics?.[key as keyof typeof cvData.metrics] ?? cvData?.[key as keyof typeof cvData];
  };

  const getCRSStatus = (score?: number) => {
    if (!score) return { label: 'Unknown', color: 'text-slate-400' };
    if (score > 0.7) return { label: 'High Risk', color: 'text-red-400' };
    if (score > 0.4) return { label: 'Moderate', color: 'text-yellow-400' };
    return { label: 'Low Risk', color: 'text-green-400' };
  };

  // Basic vitals
  const heartRate = getValue('heart_rate');
  const respiratoryRate = getValue('respiratory_rate');
  const alert = getValue('alert');

  // CRS-specific metrics
  const crsScore = getValue('crs_score');
  const faceTouchingFreq = getValue('face_touching_frequency');
  const restlessnessIndex = getValue('restlessness_index');

  // Seizure-specific metrics
  const tremorMagnitude = getValue('tremor_magnitude');
  const tremorDetected = getValue('tremor_detected');
  const movementVigor = getValue('movement_vigor');

  // Head pose (useful for both)
  const headPitch = getValue('head_pitch');
  const headYaw = getValue('head_yaw');
  const headRoll = getValue('head_roll');

  const crsStatus = getCRSStatus(crsScore);
  const hasCRS = monitoringConditions.includes('CRS');
  const hasSeizure = monitoringConditions.includes('SEIZURE');

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden"
    >
      {/* Header */}
      <div className="bg-slate-900/80 border-b border-slate-700 px-6 py-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-1">
              {patient.name}
            </h3>
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <span>Patient #{patient.id}</span>
              {patient.age && <span>• {patient.age}y/o</span>}
              {isLive && <span className="text-red-400">• 🔴 LIVE</span>}
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
            alert ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
          }`}>
            {alert ? '⚠️ Alert' : '✓ Stable'}
          </div>
        </div>
        {patient.condition && (
          <p className="text-sm text-slate-300 mt-2">
            {patient.condition}
          </p>
        )}
      </div>

      {/* Vitals Section - Only CV-Derived */}
      <div className="px-6 py-4 border-b border-slate-700">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
            Basic Vitals (CV-Derived)
          </h4>
          <span className="text-xs text-slate-500">Real-time from camera</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {/* Heart Rate */}
          <div className="bg-slate-900/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-red-400">❤️</span>
              <span className="text-xs text-slate-400">Heart Rate (rPPG)</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {heartRate ?? '--'}
            </p>
            <p className="text-xs text-slate-400 mt-1">bpm</p>
          </div>

          {/* Respiratory Rate */}
          <div className="bg-slate-900/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-blue-400">🫁</span>
              <span className="text-xs text-slate-400">Resp. Rate (Motion)</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {respiratoryRate ?? '--'}
            </p>
            <p className="text-xs text-slate-400 mt-1">breaths/min</p>
          </div>
        </div>
      </div>

      {/* CRS Monitoring Section */}
      {hasCRS && (
        <div className="px-6 py-4 border-b border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
              CRS Monitoring
            </h4>
            <span className={`text-xs font-semibold px-2 py-1 rounded ${
              (crsScore ?? 0) > 0.8 ? 'bg-red-500/20 text-red-400' :
              (crsScore ?? 0) > 0.6 ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-green-500/20 text-green-400'
            }`}>
              {crsStatus.label}
            </span>
          </div>
          <div className="space-y-3">
            {/* CRS Risk Score */}
            <div className="bg-slate-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">CRS Risk Score</span>
                <span className={`text-lg font-bold ${crsStatus.color}`}>
                  {crsScore ? `${(crsScore * 100).toFixed(0)}%` : '--'}
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                <motion.div
                  className={`h-full ${
                    (crsScore ?? 0) > 0.7 ? 'bg-red-500' :
                    (crsScore ?? 0) > 0.4 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${(crsScore ?? 0) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            {/* Face Touching & Restlessness */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Face Touching</p>
                <p className="text-2xl font-bold text-white">{faceTouchingFreq ?? 0}</p>
                <p className="text-xs text-slate-500">per minute</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Restlessness</p>
                <p className="text-2xl font-bold text-white">
                  {restlessnessIndex ? `${(restlessnessIndex * 100).toFixed(0)}%` : '0%'}
                </p>
                <p className="text-xs text-slate-500">index</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Seizure Monitoring Section */}
      {hasSeizure && (
        <div className="px-6 py-4 border-b border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
              Seizure Monitoring
            </h4>
            <span className={`text-xs font-semibold px-2 py-1 rounded ${
              tremorDetected ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
            }`}>
              {tremorDetected ? 'Tremor Detected' : 'Normal'}
            </span>
          </div>
          <div className="space-y-3">
            {/* Tremor & Movement */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Tremor Magnitude</p>
                <p className="text-2xl font-bold text-white">
                  {tremorMagnitude ? tremorMagnitude.toFixed(1) : '0.0'}
                </p>
                <p className="text-xs text-slate-500">amplitude</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Movement Vigor</p>
                <p className="text-2xl font-bold text-white">
                  {movementVigor ? movementVigor.toFixed(1) : '0.0'}
                </p>
                <p className="text-xs text-slate-500">index</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Head Pose (shown for all) */}
      {monitoringConditions.length > 0 && (
        <div className="px-6 py-4 border-b border-slate-700">
          <h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
            Head Orientation
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400 mb-1">Pitch</p>
              <p className="text-xl font-bold text-white">
                {headPitch ? `${headPitch.toFixed(1)}°` : '--'}
              </p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400 mb-1">Yaw</p>
              <p className="text-xl font-bold text-white">
                {headYaw ? `${headYaw.toFixed(1)}°` : '--'}
              </p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400 mb-1">Roll</p>
              <p className="text-xl font-bold text-white">
                {headRoll ? `${headRoll.toFixed(1)}°` : '--'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* No Monitoring Protocols Message */}
      {monitoringConditions.length === 0 && (
        <div className="px-6 py-8 border-b border-slate-700">
          <div className="text-center">
            <p className="text-slate-400 text-sm mb-2">No condition-specific monitoring active</p>
            <p className="text-slate-500 text-xs">Basic vitals will continue to be tracked</p>
          </div>
        </div>
      )}

      {/* AI Status */}
      <div className="px-6 py-4 border-b border-slate-700">
        <div className="flex items-center gap-3 text-sm">
          <motion.div
            className="w-3 h-3 bg-green-500 rounded-full"
            animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
          />
          <span className="text-slate-300">CV Monitoring Active</span>
          {monitoringConditions.length > 0 && (
            <span className="text-slate-500">• {monitoringConditions.join(', ')}</span>
          )}
        </div>
      </div>

      {/* Recent Events Section */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Recent Events
        </h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {alert ? (
            <div className="flex gap-3 text-sm">
              <span className="text-slate-500 flex-shrink-0">
                {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </span>
              <div>
                <span className="text-red-400 font-semibold">⚠️ CRS Alert Detected</span>
                <p className="text-slate-400 text-xs mt-1">
                  CRS risk elevated to {crsScore ? `${(crsScore * 100).toFixed(0)}%` : 'unknown'}
                </p>
              </div>
            </div>
          ) : null}

          <div className="flex gap-3 text-sm">
            <span className="text-slate-500 flex-shrink-0">
              {new Date(Date.now() - 120000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
            <div>
              <span className="text-slate-300">Vitals Normal</span>
              <p className="text-slate-400 text-xs mt-1">All parameters within range</p>
            </div>
          </div>

          <div className="flex gap-3 text-sm">
            <span className="text-slate-500 flex-shrink-0">
              {new Date(Date.now() - 300000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
            <div>
              <span className="text-slate-300">Monitoring Started</span>
              <p className="text-slate-400 text-xs mt-1">AI analysis initialized</p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="px-6 py-4 bg-slate-900/50 border-t border-slate-700">
        <button className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-semibold transition-colors">
          View Full History
        </button>
      </div>
    </motion.div>
  );
}
