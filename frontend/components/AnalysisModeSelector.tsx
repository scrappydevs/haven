'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export type AnalysisMode = 'normal' | 'enhanced';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

interface AnalysisModeSelectorProps {
  patient: Patient;
  onConfirm: (mode: AnalysisMode) => void;
  onBack: () => void;
  initialMode?: AnalysisMode;
}

export default function AnalysisModeSelector({ patient, onConfirm, onBack, initialMode }: AnalysisModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<AnalysisMode>(initialMode ?? 'enhanced');

  useEffect(() => {
    setSelectedMode(initialMode ?? 'enhanced');
  }, [initialMode, patient]);

  return (
    <div className="bg-surface border border-neutral-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-8 border-b border-neutral-200">
        <div className="flex items-start gap-4 mb-6">
          <img
            src={patient.photo_url}
            alt={patient.name}
            className="w-16 h-16 object-cover rounded-lg"
          />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-xl font-light text-neutral-950">{patient.name}</h3>
              <span className="label-uppercase bg-primary-700 text-white px-2 py-1 text-xs">
                {patient.patient_id}
              </span>
            </div>
            <p className="text-sm text-neutral-600">
              {patient.age}y/o • {patient.gender}
            </p>
          </div>
        </div>
        <h2 className="text-2xl font-light tracking-tight text-neutral-950">
          Select Monitoring Mode
        </h2>
        <p className="text-sm text-neutral-600 mt-2">
          Choose how you want to monitor this patient
        </p>
      </div>

      {/* Mode Selection */}
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Normal Mode */}
          <motion.button
            onClick={() => setSelectedMode('normal')}
            className={`relative p-6 border-2 rounded-lg text-left transition-all ${
              selectedMode === 'normal'
                ? 'border-primary-700 bg-white'
                : 'border-neutral-200 bg-white hover:border-neutral-400'
            }`}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Selection Indicator */}
            {selectedMode === 'normal' && (
              <div className="absolute top-4 right-4 w-6 h-6 bg-primary-700 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}

            {/* Icon */}
            <div className="w-12 h-12 bg-neutral-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-neutral-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>

            <h3 className="text-lg font-medium text-neutral-950 mb-2">Normal Mode</h3>
            <p className="text-sm text-neutral-600 mb-4">
              Basic webcam monitoring without AI analysis
            </p>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Live video feed</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Lower bandwidth usage</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span>No AI analysis</span>
              </div>
            </div>
          </motion.button>

          {/* Enhanced Mode */}
          <motion.button
            onClick={() => setSelectedMode('enhanced')}
            className={`relative p-6 border-2 rounded-lg text-left transition-all ${
              selectedMode === 'enhanced'
                ? 'border-primary-700 bg-white'
                : 'border-neutral-200 bg-white hover:border-neutral-400'
            }`}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Selection Indicator */}
            {selectedMode === 'enhanced' && (
              <div className="absolute top-4 right-4 w-6 h-6 bg-primary-700 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}

            {/* Icon */}
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
              </svg>
            </div>

            <h3 className="text-lg font-medium text-neutral-950 mb-2">Enhanced Mode</h3>
            <p className="text-sm text-neutral-600 mb-4">
              AI-powered monitoring with real-time analysis
            </p>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-neutral-700">
                <svg className="w-4 h-4 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Fall detection</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-700">
                <svg className="w-4 h-4 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Movement tracking</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-700">
                <svg className="w-4 h-4 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Anomaly detection</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-700">
                <svg className="w-4 h-4 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Real-time alerts</span>
              </div>
            </div>

            {/* Recommended Badge */}
            <div className="absolute top-4 left-4 bg-primary-700 text-white text-xs font-medium px-2 py-1 rounded">
              RECOMMENDED
            </div>
          </motion.button>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-6 bg-neutral-50 border-t border-neutral-200 flex items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-neutral-300 text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 label-uppercase text-sm transition-colors"
        >
          Back
        </button>
        <button
          onClick={() => onConfirm(selectedMode)}
          className="px-8 py-3 bg-primary-700 hover:bg-primary-900 text-white label-uppercase text-sm transition-colors hover-lift"
        >
          Confirm & Continue
        </button>
      </div>
    </div>
  );
}
