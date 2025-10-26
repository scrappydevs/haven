'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';
import HandoffFormModal from './HandoffFormModal';

interface HandoffForm {
  id: string;
  form_number: string;
  patient_id: string;
  alert_ids: string[];
  content: {
    patient_info: {
      name?: string;
      patient_id: string;
    };
    primary_concern: string;
    severity_level: string;
    generated_at: string;
  };
  status: string;
  created_at: string;
}

interface HandoffFormsListProps {
  limit?: number;
  refreshInterval?: number; // in milliseconds
}

export default function HandoffFormsList({ limit = 10, refreshInterval = 30000 }: HandoffFormsListProps) {
  const [forms, setForms] = useState<HandoffForm[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFormId, setSelectedFormId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchForms();

    // Set up auto-refresh
    const interval = setInterval(fetchForms, refreshInterval);
    return () => clearInterval(interval);
  }, [limit, refreshInterval]);

  const fetchForms = async () => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/handoff-agent/forms?limit=${limit}`);
      const data = await response.json();
      setForms(data.forms || []);
    } catch (error) {
      console.error('Error fetching handoff forms:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormClick = (formId: string) => {
    setSelectedFormId(formId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedFormId(null);
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'border-red-500 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-green-500 bg-green-50',
      info: 'border-blue-500 bg-blue-50',
    };
    return colors[severity.toLowerCase()] || 'border-neutral-300 bg-neutral-50';
  };

  const getSeverityBadge = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-neutral-900',
      low: 'bg-green-500 text-white',
      info: 'bg-blue-500 text-white',
    };
    return colors[severity.toLowerCase()] || 'bg-neutral-500 text-white';
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <>
      <div className="bg-surface border border-neutral-200 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
          <h2 className="text-xs font-medium uppercase tracking-wider text-neutral-950">
            Handoff Forms
          </h2>
          <div className="px-2 py-0.5 bg-accent-terra/10 border border-accent-terra">
            <span className="text-accent-terra text-[10px] font-medium">{forms.length}</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin h-4 w-4 border-2 border-neutral-300 border-t-neutral-950 rounded-full"></div>
            </div>
          ) : forms.length === 0 ? (
            <div className="text-center py-8 border border-neutral-200 bg-neutral-50">
              <p className="text-neutral-500 text-xs font-light">No handoff forms yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              <AnimatePresence>
                {forms.map((form, idx) => (
                  <motion.button
                    key={form.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    transition={{ delay: idx * 0.02 }}
                    onClick={() => handleFormClick(form.id)}
                    className={`w-full text-left border-l-4 ${getSeverityColor(
                      form.content.severity_level
                    )} border border-neutral-200 p-3 hover:border-neutral-950 transition-all`}
                  >
                    {/* Single Row: Form Number + Time */}
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono text-neutral-500 tracking-tight">
                        {form.form_number}
                      </span>
                      <span className="text-[10px] text-neutral-400">
                        {getTimeAgo(form.content.generated_at)}
                      </span>
                    </div>

                    {/* Patient Name + Severity Badge */}
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-xs font-medium text-neutral-950 truncate flex-1">
                        {form.content.patient_info.name || form.content.patient_info.patient_id}
                      </p>
                      <span
                        className={`px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ml-2 ${getSeverityBadge(
                          form.content.severity_level
                        )}`}
                      >
                        {form.content.severity_level}
                      </span>
                    </div>

                    {/* Primary Concern - Single Line */}
                    <p className="text-[11px] text-neutral-600 font-light truncate">
                      {form.content.primary_concern}
                    </p>
                  </motion.button>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      <HandoffFormModal formId={selectedFormId} isOpen={isModalOpen} onClose={handleCloseModal} />
    </>
  );
}
