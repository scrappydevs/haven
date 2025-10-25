'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';

// Hardcoded nurse list for MVP
const NURSES = [
  { name: 'Nurse Sarah Johnson', phone: '+14155551234' },
  { name: 'Nurse Michael Chen', phone: '+14155555678' },
  { name: 'Nurse Emily Rodriguez', phone: '+14155559012' },
  { name: 'Dr. David Kim (On-Call)', phone: '+14155553456' },
];

interface ToastMessage {
  id: string;
  type: 'success' | 'error';
  message: string;
}

export default function ManualAlertsPanel() {
  const [selectedNurse, setSelectedNurse] = useState('');
  const [customMessage, setCustomMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (type: 'success' | 'error', message: string) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, type, message }]);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  const handleSendAlert = async () => {
    if (!selectedNurse || !customMessage.trim()) {
      showToast('error', 'Please select a nurse and enter a message');
      return;
    }

    setIsSending(true);

    try {
      const API_URL = getApiUrl();
      const response = await fetch(`${API_URL}/alerts/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: selectedNurse,
          message: customMessage,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send alert');
      }

      const data = await response.json();
      
      showToast('success', `✅ Alert sent to ${NURSES.find(n => n.phone === selectedNurse)?.name}`);
      
      // Clear form
      setCustomMessage('');
      
    } catch (error) {
      console.error('Error sending alert:', error);
      showToast('error', '❌ Failed to send alert. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <>
      <div className="bg-white border border-neutral-200 p-6">
        {/* Header */}
        <div className="mb-6 pb-4 border-b border-neutral-200">
          <h2 className="text-xl font-light uppercase tracking-wider text-neutral-950 mb-1">
            Manual Alerts
          </h2>
          <p className="text-xs text-neutral-600 font-light">
            Send SMS notifications to nursing staff
          </p>
        </div>

        {/* Nurse Selection */}
        <div className="mb-4">
          <label className="block text-xs font-medium uppercase tracking-wider text-neutral-700 mb-2">
            Select Recipient
          </label>
          <select
            value={selectedNurse}
            onChange={(e) => setSelectedNurse(e.target.value)}
            className="w-full border border-neutral-300 px-4 py-2.5 text-sm focus:outline-none focus:border-neutral-950 transition-colors bg-white"
            disabled={isSending}
          >
            <option value="">Choose a nurse...</option>
            {NURSES.map((nurse) => (
              <option key={nurse.phone} value={nurse.phone}>
                {nurse.name} ({nurse.phone})
              </option>
            ))}
          </select>
        </div>

        {/* Message Input */}
        <div className="mb-4">
          <label className="block text-xs font-medium uppercase tracking-wider text-neutral-700 mb-2">
            Message
          </label>
          <textarea
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="Enter alert message (e.g., Patient P-001 showing elevated CRS score...)"
            className="w-full border border-neutral-300 px-4 py-2.5 text-sm focus:outline-none focus:border-neutral-950 transition-colors resize-none bg-white"
            rows={4}
            disabled={isSending}
            maxLength={160}
          />
          <p className="text-xs text-neutral-500 mt-1 font-light">
            {customMessage.length}/160 characters
          </p>
        </div>

        {/* Send Button */}
        <button
          onClick={handleSendAlert}
          disabled={isSending || !selectedNurse || !customMessage.trim()}
          className={`w-full px-6 py-3 text-sm font-medium uppercase tracking-wider transition-all
            ${isSending || !selectedNurse || !customMessage.trim()
              ? 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
              : 'bg-neutral-950 text-white hover:bg-neutral-800'
            }`}
        >
          {isSending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Sending...
            </span>
          ) : (
            'Send Alert'
          )}
        </button>

        {/* Info Notice */}
        <div className="mt-4 p-3 bg-neutral-50 border border-neutral-200">
          <p className="text-xs text-neutral-600 font-light">
            <span className="font-medium">Note:</span> This will send an SMS via Twilio. 
            In production, alerts will be triggered automatically by the AI when anomalies are detected.
          </p>
        </div>
      </div>

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`px-6 py-4 shadow-lg border-2 min-w-[300px] ${
                toast.type === 'success'
                  ? 'bg-green-50 border-green-500 text-green-900'
                  : 'bg-red-50 border-red-500 text-red-900'
              }`}
            >
              <p className="text-sm font-medium">{toast.message}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
}

