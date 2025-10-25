'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { getApiUrl } from '@/lib/api';

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
    const apiUrl = getApiUrl();

    // Fetch available protocols
    fetch(`${apiUrl}/monitoring/protocols`)
      .then(res => res.json())
      .then(data => {
        setProtocols(data);
      })
      .catch(err => console.error('Error fetching protocols:', err));

    // Get AI recommendations
    setLoading(true);
    fetch(`${apiUrl}/monitoring/recommend`, {
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
    <div className="bg-white border border-neutral-200 p-8 rounded-lg">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="mb-6 text-neutral-700 hover:text-neutral-950 transition-colors flex items-center gap-3 text-sm font-medium"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="square" strokeLinejoin="miter" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Patient Selection
      </button>

      {/* Patient Card */}
      <div className="bg-neutral-50 border border-neutral-200 p-4 mb-6 rounded-lg">
        <div className="flex items-center gap-4">
          <img
            src={patient.photo_url}
            alt={patient.name}
            className="w-16 h-16 object-cover rounded-lg"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-medium text-neutral-950">{patient.name}</h3>
              <span className="bg-primary-700 text-white px-2 py-1 rounded text-xs">
                {patient.patient_id}
              </span>
            </div>
            <p className="text-sm text-neutral-700">{patient.age}y/o • {patient.gender}</p>
            <p className="text-sm text-neutral-950 font-medium">{patient.condition}</p>
          </div>
        </div>
      </div>


      {/* Monitoring Protocol Selection */}
      <div className="mb-8">
        <h4 className="text-base font-medium text-neutral-950 mb-6 border-b-2 border-neutral-950 pb-3">Select Monitoring Protocols</h4>
        <div className="space-y-4">
          {Object.entries(protocols).map(([key, protocol]) => {
            const isRecommended = aiRecommendations.includes(key);
            const isSelected = selectedConditions.includes(key);

            return (
              <motion.button
                key={key}
                onClick={() => toggleCondition(key)}
                className={`w-full text-left p-6 border transition-all rounded-lg ${
                  isSelected
                    ? 'bg-primary-100 border-primary-700'
                    : 'bg-neutral-50 border-neutral-200 hover:border-neutral-400'
                }`}
                whileHover={{ scale: 1.005 }}
                whileTap={{ scale: 0.995 }}
              >
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <div className={`w-6 h-6 border-2 flex items-center justify-center flex-shrink-0 mt-1 rounded ${
                    isSelected ? 'bg-primary-700 border-primary-700' : 'border-neutral-300'
                  }`}>
                    {isSelected && (
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                        <path strokeLinecap="square" strokeLinejoin="miter" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h5 className="text-base font-medium text-neutral-950">{protocol.label}</h5>
                      {isRecommended && (
                        <span className="text-white px-2 py-1 rounded text-xs" style={{backgroundColor: '#334155'}}>
                          AI Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-neutral-700 mb-3">{protocol.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {protocol.metrics.slice(0, 3).map(metric => (
                        <span key={metric} className="bg-neutral-100 text-neutral-700 px-2 py-1 border border-neutral-200 rounded text-xs">
                          {metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                      {protocol.metrics.length > 3 && (
                        <span className="text-neutral-500 text-xs">
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
        <div className="bg-accent-sand border-l-4 border-accent-terra p-4 mb-6">
          <p className="text-sm text-neutral-950">
            <span className="font-semibold">Note:</span> No monitoring protocols selected. Basic vitals will still be tracked.
          </p>
        </div>
      )}

      {/* Confirm Button */}
      <button
        onClick={() => onConfirm(selectedConditions)}
        className="w-full py-4 bg-primary-700 hover:bg-primary-900 text-white label-uppercase transition-all border border-primary-700 hover:border-primary-900 hover-lift rounded-lg"
      >
        Start Streaming with Selected Protocols
      </button>
    </div>
  );
}
