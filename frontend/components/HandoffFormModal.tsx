'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { getApiUrl } from '@/lib/api';

interface HandoffForm {
  id: string;
  form_number: string;
  patient_id: string;
  alert_ids: string[];
  content: {
    patient_info: {
      patient_id: string;
      name?: string;
      age?: number;
      room_number?: string;
      diagnosis?: string;
    };
    alert_summary: string;
    primary_concern: string;
    severity_level: string;
    recommended_actions: string[];
    urgency_notes?: string;
    related_alerts: any[];
    generated_at: string;
  };
  status: string;
  created_at: string;
  pdf_path?: string;
}

interface HandoffFormModalProps {
  formId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onAcknowledge?: () => void; // Callback to refresh list
}

export default function HandoffFormModal({ formId, isOpen, onClose, onAcknowledge }: HandoffFormModalProps) {
  const [form, setForm] = useState<HandoffForm | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isAcknowledging, setIsAcknowledging] = useState(false);

  useEffect(() => {
    if (formId && isOpen) {
      fetchFormDetails();
    }
  }, [formId, isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const fetchFormDetails = async () => {
    setIsLoading(true);
    try {
      const apiUrl = getApiUrl();
      // Fetch alert details directly
      const response = await fetch(`${apiUrl}/alerts/${formId}`);
      if (!response.ok) throw new Error('Alert not found');

      const alertData = await response.json();

      // Transform alert into form-like structure for display
      const transformedForm = {
        id: alertData.id,
        form_number: `ALERT-${alertData.id.substring(0, 8)}`,
        patient_id: alertData.patient_id || 'Unknown',
        alert_ids: [alertData.id],
        content: {
          patient_info: {
            patient_id: alertData.patient_id || 'Unknown',
            name: alertData.patient_id || 'Unknown',
            age: null,
            room_number: alertData.room_id || null,
          },
          primary_concern: alertData.title,
          alert_summary: alertData.description || alertData.title,
          severity_level: alertData.severity,
          recommended_actions: ['Review alert details', 'Assess patient condition', 'Take appropriate action'],
          urgency_notes: alertData.severity === 'critical' ? 'Immediate attention required' : null,
          related_alerts: [alertData],
          generated_at: alertData.triggered_at || alertData.created_at,
        },
        status: alertData.status,
        created_at: alertData.created_at,
      };

      setForm(transformedForm as any);
    } catch (error) {
      console.error('Error fetching alert details:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!formId) return;

    setIsDownloading(true);
    try {
      const apiUrl = getApiUrl();
      console.log('[PDF Download] Starting PDF generation for alert:', formId);

      // Generate PDF on-the-fly for this alert
      const response = await fetch(`${apiUrl}/handoff-agent/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_ids: [formId] }),
      });

      console.log('[PDF Download] Generate response status:', response.status);
      const data = await response.json();
      console.log('[PDF Download] Generate response data:', data);

      if (data.success && data.pdf_path) {
        console.log('[PDF Download] PDF generated successfully, downloading from form_id:', data.form_id);

        // Now download the generated PDF
        const pdfResponse = await fetch(`${apiUrl}/handoff-agent/forms/${data.form_id}/pdf`);
        console.log('[PDF Download] Download response status:', pdfResponse.status);

        if (!pdfResponse.ok) {
          const errorText = await pdfResponse.text();
          console.error('[PDF Download] Download failed:', errorText);
          throw new Error(`Download failed: ${errorText}`);
        }

        const blob = await pdfResponse.blob();
        console.log('[PDF Download] PDF blob received, size:', blob.size);

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.form_number || 'alert'}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log('[PDF Download] Download complete!');
      } else {
        console.error('[PDF Download] Generation failed:', data.message || 'Unknown error');
        throw new Error(data.message || 'Failed to generate PDF');
      }
    } catch (error) {
      console.error('[PDF Download] Error:', error);
      alert(`Failed to download PDF. Please try again.\n\nError: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!formId) return;

    setIsAcknowledging(true);
    try {
      const apiUrl = getApiUrl();
      // Update alert status directly
      const response = await fetch(`${apiUrl}/alerts/${formId}/acknowledge`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.success || response.ok) {
        alert(`✅ Alert acknowledged`);
        onClose();
        if (onAcknowledge) {
          onAcknowledge(); // Trigger refresh
        }
      } else {
        alert(`Failed to acknowledge: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      alert('Failed to acknowledge. Please try again.');
    } finally {
      setIsAcknowledging(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-neutral-900',
      low: 'bg-green-500 text-white',
      info: 'bg-blue-500 text-white',
    };
    return colors[severity.toLowerCase()] || 'bg-neutral-500 text-white';
  };

  if (!isOpen || !formId) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-40 bg-neutral-950/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <div className="w-full max-w-2xl bg-white border-2 border-neutral-950 shadow-2xl max-h-[90vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b-2 border-neutral-950 bg-neutral-50">
                <div>
                  <h2 className="text-xl font-medium uppercase tracking-wider text-neutral-950">
                    Handoff Form
                  </h2>
                  {form && (
                    <p className="text-sm text-neutral-600 mt-1 font-mono">
                      {form.form_number}
                    </p>
                  )}
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-neutral-200 rounded-full transition-colors"
                  aria-label="Close"
                >
                  <svg className="w-5 h-5" viewBox="0 0 16 16" fill="none">
                    <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto px-6 py-6">
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin h-8 w-8 border-4 border-neutral-950 border-t-transparent rounded-full"></div>
                  </div>
                ) : form ? (
                  <div className="space-y-6">
                    {/* Patient Info */}
                    <div className="border-l-4 border-neutral-950 pl-4">
                      <h3 className="text-sm font-medium uppercase tracking-wider text-neutral-700 mb-2">
                        Patient Information
                      </h3>
                      <p className="text-lg font-medium text-neutral-950">
                        {form.content.patient_info.name || form.content.patient_info.patient_id}
                      </p>
                      <div className="flex gap-4 mt-2 text-sm text-neutral-600">
                        {form.content.patient_info.age && (
                          <span>Age: {form.content.patient_info.age}</span>
                        )}
                        {form.content.patient_info.room_number && (
                          <span>Room: {form.content.patient_info.room_number}</span>
                        )}
                      </div>
                    </div>

                    {/* Severity Badge */}
                    <div>
                      <span
                        className={`inline-block px-4 py-2 text-xs font-bold uppercase tracking-wider ${getSeverityColor(
                          form.content.severity_level
                        )}`}
                      >
                        {form.content.severity_level} Severity
                      </span>
                    </div>

                    {/* Primary Concern */}
                    <div>
                      <h3 className="text-sm font-medium uppercase tracking-wider text-neutral-700 mb-2">
                        Primary Concern
                      </h3>
                      <p className="text-base text-neutral-950 font-medium">
                        {form.content.primary_concern}
                      </p>
                    </div>

                    {/* Alert Summary */}
                    <div>
                      <h3 className="text-sm font-medium uppercase tracking-wider text-neutral-700 mb-2">
                        Summary
                      </h3>
                      <p className="text-sm text-neutral-700 leading-relaxed">
                        {form.content.alert_summary}
                      </p>
                    </div>

                    {/* Urgency Notes */}
                    {form.content.urgency_notes && (
                      <div className="bg-red-50 border-l-4 border-red-500 p-4">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-red-900 mb-2">
                          ⚠️ Urgent
                        </h3>
                        <p className="text-sm text-red-800">{form.content.urgency_notes}</p>
                      </div>
                    )}

                    {/* Recommended Actions */}
                    <div>
                      <h3 className="text-sm font-medium uppercase tracking-wider text-neutral-700 mb-2">
                        Recommended Actions
                      </h3>
                      <ol className="space-y-2">
                        {form.content.recommended_actions.map((action, idx) => (
                          <li key={idx} className="text-sm text-neutral-700 flex gap-3">
                            <span className="font-bold text-neutral-950">{idx + 1}.</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Related Alerts Count */}
                    <div className="bg-neutral-50 border border-neutral-200 p-4">
                      <p className="text-sm text-neutral-700">
                        <span className="font-medium">Related Alerts:</span>{' '}
                        {form.content.related_alerts.length} alert(s) included in this handoff
                      </p>
                    </div>

                    {/* Metadata */}
                    <div className="text-xs text-neutral-500 pt-4 border-t border-neutral-200">
                      <p>Generated: {new Date(form.content.generated_at).toLocaleString()}</p>
                      <p>Status: {form.status}</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-neutral-600">Form not found</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t-2 border-neutral-950 bg-neutral-50 flex gap-3">
                <button
                  onClick={handleAcknowledge}
                  disabled={isAcknowledging || !form}
                  className={`flex-1 px-6 py-3 text-sm font-bold uppercase tracking-wider transition-all ${
                    isAcknowledging || !form
                      ? 'bg-green-300 text-green-700 cursor-not-allowed'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isAcknowledging ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Acknowledging...
                    </span>
                  ) : (
                    <>✓ Acknowledge</>
                  )}
                </button>
                <button
                  onClick={handleDownloadPDF}
                  disabled={isDownloading || !form}
                  className={`flex-1 px-6 py-3 text-sm font-bold uppercase tracking-wider transition-all ${
                    isDownloading || !form
                      ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed'
                      : 'bg-neutral-950 text-white hover:bg-neutral-800'
                  }`}
                >
                  {isDownloading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Downloading...
                    </span>
                  ) : (
                    <>📥 Download PDF</>
                  )}
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-3 text-sm font-bold uppercase tracking-wider border-2 border-neutral-950 text-neutral-950 hover:bg-neutral-950 hover:text-white transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
