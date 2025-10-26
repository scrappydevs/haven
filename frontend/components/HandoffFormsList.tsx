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
      <div className="bg-white border-2 border-neutral-950 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-neutral-950 bg-neutral-50">
          <h2 className="text-lg font-medium uppercase tracking-wider text-neutral-950">
            Handoff Forms
          </h2>
          <div className="px-3 py-1 bg-neutral-950 text-white text-xs font-bold">
            {forms.length}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-6 w-6 border-2 border-neutral-950 border-t-transparent rounded-full"></div>
            </div>
          ) : forms.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-neutral-300">
              <p className="text-neutral-500 text-sm font-light">No handoff forms yet</p>
              <p className="text-neutral-400 text-xs mt-1">Forms will appear here when alerts are generated</p>
            </div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {forms.map((form, idx) => (
                  <motion.button
                    key={form.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: idx * 0.03 }}
                    onClick={() => handleFormClick(form.id)}
                    className={`w-full text-left border-l-4 ${getSeverityColor(
                      form.content.severity_level
                    )} border border-neutral-200 p-4 hover:shadow-md transition-all group`}
                  >
                    {/* Top Row: Form Number + Time */}
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-neutral-600 font-medium">
                        {form.form_number}
                      </span>
                      <span className="text-xs text-neutral-500">
                        {getTimeAgo(form.content.generated_at)}
                      </span>
                    </div>

                    {/* Patient Name */}
                    <p className="text-sm font-medium text-neutral-950 mb-1">
                      {form.content.patient_info.name || form.content.patient_info.patient_id}
                    </p>

                    {/* Primary Concern - Truncated */}
                    <p className="text-xs text-neutral-700 mb-2 line-clamp-2">
                      {form.content.primary_concern}
                    </p>

                    {/* Bottom Row: Severity Badge + Alerts Count */}
                    <div className="flex items-center justify-between">
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getSeverityBadge(
                          form.content.severity_level
                        )}`}
                      >
                        {form.content.severity_level}
                      </span>
                      <span className="text-xs text-neutral-500">
                        {form.alert_ids.length} alert{form.alert_ids.length !== 1 ? 's' : ''}
                      </span>
                    </div>

                    {/* Hover indicator */}
                    <div className="mt-2 pt-2 border-t border-neutral-200 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-xs text-neutral-600 font-medium">
                        Click to view details →
                      </span>
                    </div>
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
