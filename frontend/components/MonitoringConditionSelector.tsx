'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

interface Protocol {
  label: string;
  description: string;
  metrics: string[];
}

interface MonitoringConditionSelectorProps {
  patient: Patient;
  onConfirm: (conditions: string[]) => void;
  onBack: () => void;
}

export default function MonitoringConditionSelector({ patient, onConfirm, onBack }: MonitoringConditionSelectorProps) {
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [aiRecommendations, setAiRecommendations] = useState<string[]>([]);
  const [aiReasoning, setAiReasoning] = useState<string>('');
  const [aiMethod, setAiMethod] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [protocols, setProtocols] = useState<Record<string, Protocol>>({});

  useEffect(() => {
    // Fetch available protocols
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/monitoring/protocols`)
      .then(res => res.json())
      .then(data => {
        setProtocols(data);
      })
      .catch(err => console.error('Error fetching protocols:', err));

    // Get AI recommendations
    setLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/monitoring/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: patient.patient_id,
        name: patient.name,
        age: patient.age,
        gender: patient.gender,
        condition: patient.condition
      })
    })
      .then(res => res.json())
      .then(data => {
        setAiRecommendations(data.recommended || []);
        setAiReasoning(data.reasoning || '');
        setAiMethod(data.method || 'keyword');
        // Auto-select AI recommendations
        setSelectedConditions(data.recommended || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error getting AI recommendations:', err);
        setLoading(false);
      });
  }, [patient]);

  const toggleCondition = (condition: string) => {
    setSelectedConditions(prev =>
      prev.includes(condition)
        ? prev.filter(c => c !== condition)
        : [...prev, condition]
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="mb-4 text-slate-400 hover:text-white transition-colors flex items-center gap-2"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Patient Selection
      </button>

      {/* Patient Card */}
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <img
            src={patient.photo_url}
            alt={patient.name}
            className="w-16 h-16 rounded-full object-cover border-2 border-blue-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-semibold text-white">{patient.name}</h3>
              <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
                {patient.patient_id}
              </span>
            </div>
            <p className="text-sm text-slate-400">
              {patient.age}y/o • {patient.gender}
            </p>
            <p className="text-sm text-slate-300 mt-1">{patient.condition}</p>
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      {loading ? (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-blue-400">AI is analyzing patient condition...</span>
          </div>
        </div>
      ) : aiRecommendations.length > 0 ? (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3 mb-2">
            <span className="text-2xl">💡</span>
            <div className="flex-1">
              <h4 className="text-blue-400 font-semibold mb-1">
                AI Recommendation {aiMethod === 'llm' && '(Claude)'}
              </h4>
              <p className="text-sm text-slate-300">{aiReasoning}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-slate-400">Suggested protocols:</span>
                {aiRecommendations.map(rec => (
                  <span key={rec} className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                    {protocols[rec]?.label || rec}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Monitoring Protocol Selection */}
      <div className="mb-6">
        <h4 className="text-white font-semibold mb-3">Select Monitoring Protocols</h4>
        <div className="space-y-3">
          {Object.entries(protocols).map(([key, protocol]) => {
            const isRecommended = aiRecommendations.includes(key);
            const isSelected = selectedConditions.includes(key);

            return (
              <motion.button
                key={key}
                onClick={() => toggleCondition(key)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  isSelected
                    ? 'bg-blue-500/20 border-blue-500'
                    : 'bg-slate-900/50 border-slate-700 hover:border-slate-600'
                }`}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox */}
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 ${
                    isSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-600'
                  }`}>
                    {isSelected && (
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="text-white font-semibold">{protocol.label}</h5>
                      {isRecommended && (
                        <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">
                          AI Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400 mb-2">{protocol.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {protocol.metrics.slice(0, 3).map(metric => (
                        <span key={metric} className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                          {metric.replace(/_/g, ' ')}
                        </span>
                      ))}
                      {protocol.metrics.length > 3 && (
                        <span className="text-xs text-slate-500">
                          +{protocol.metrics.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Info Message */}
      {selectedConditions.length === 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4">
          <p className="text-sm text-yellow-400">
            ⚠️ No monitoring protocols selected. Basic vitals will still be tracked.
          </p>
        </div>
      )}

      {/* Confirm Button */}
      <button
        onClick={() => onConfirm(selectedConditions)}
        className="w-full py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors"
      >
        Start Streaming with Selected Protocols
      </button>
    </div>
  );
}
