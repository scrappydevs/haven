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
    <div className="bg-white border-4 border-neutral-950 p-8">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="mb-6 text-neutral-700 hover:text-neutral-950 transition-colors flex items-center gap-3 label-uppercase"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="square" strokeLinejoin="miter" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Patient Selection
      </button>

      {/* Patient Card */}
      <div className="bg-neutral-50 border-2 border-neutral-950 p-6 mb-8">
        <div className="flex items-center gap-6">
          <img
            src={patient.photo_url}
            alt={patient.name}
            className="w-20 h-20 object-cover border-2 border-neutral-950"
          />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="heading-section text-neutral-950">{patient.name}</h3>
              <span className="label-uppercase bg-primary-700 text-white px-3 py-1">
                {patient.patient_id}
              </span>
            </div>
            <p className="body-default text-neutral-700 mb-1">
              {patient.age}y/o • {patient.gender}
            </p>
            <p className="body-default text-neutral-950 font-medium">{patient.condition}</p>
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      {loading ? (
        <div className="bg-primary-100 border-2 border-primary-700 p-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-primary-700 border-t-transparent animate-spin" />
            <span className="label-uppercase text-primary-950">AI is analyzing patient condition...</span>
          </div>
        </div>
      ) : aiRecommendations.length > 0 ? (
        <div className="bg-primary-100 border-l-4 border-primary-700 p-6 mb-8">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary-700 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-lg">✓</span>
            </div>
            <div className="flex-1">
              <h4 className="heading-subsection text-neutral-950 mb-2">
                AI Recommendation {aiMethod === 'llm' && '(Claude)'}
              </h4>
              <p className="body-default text-neutral-950 mb-3">{aiReasoning}</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="label-uppercase text-neutral-700">Suggested:</span>
                {aiRecommendations.map(rec => (
                  <span key={rec} className="label-uppercase bg-primary-700 text-white px-3 py-1">
                    {protocols[rec]?.label || rec}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Monitoring Protocol Selection */}
      <div className="mb-8">
        <h4 className="heading-section text-neutral-950 mb-6 border-b-2 border-neutral-950 pb-3">Select Monitoring Protocols</h4>
        <div className="space-y-4">
          {Object.entries(protocols).map(([key, protocol]) => {
            const isRecommended = aiRecommendations.includes(key);
            const isSelected = selectedConditions.includes(key);

            return (
              <motion.button
                key={key}
                onClick={() => toggleCondition(key)}
                className={`w-full text-left p-6 border-2 transition-all ${
                  isSelected
                    ? 'bg-primary-100 border-primary-700'
                    : 'bg-neutral-50 border-neutral-950 hover:border-neutral-700'
                }`}
                whileHover={{ scale: 1.005 }}
                whileTap={{ scale: 0.995 }}
              >
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <div className={`w-6 h-6 border-2 flex items-center justify-center flex-shrink-0 mt-1 ${
                    isSelected ? 'bg-primary-700 border-primary-700' : 'border-neutral-950'
                  }`}>
                    {isSelected && (
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                        <path strokeLinecap="square" strokeLinejoin="miter" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h5 className="heading-subsection text-neutral-950">{protocol.label}</h5>
                      {isRecommended && (
                        <span className="label-uppercase bg-accent-terra text-white px-2 py-1">
                          AI Recommended
                        </span>
                      )}
                    </div>
                    <p className="body-default text-neutral-700 mb-3">{protocol.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {protocol.metrics.slice(0, 3).map(metric => (
                        <span key={metric} className="label-uppercase bg-neutral-100 text-neutral-700 px-2 py-1 border border-neutral-950">
                          {metric.replace(/_/g, ' ')}
                        </span>
                      ))}
                      {protocol.metrics.length > 3 && (
                        <span className="label-uppercase text-neutral-500">
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
          <p className="body-default text-neutral-950">
            <span className="font-semibold">Note:</span> No monitoring protocols selected. Basic vitals will still be tracked.
          </p>
        </div>
      )}

      {/* Confirm Button */}
      <button
        onClick={() => onConfirm(selectedConditions)}
        className="w-full py-4 bg-primary-700 hover:bg-primary-900 text-white label-uppercase transition-all border-2 border-primary-700 hover:border-primary-900 hover-lift"
      >
        Start Streaming with Selected Protocols
      </button>
    </div>
  );
}
