'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';

// Hardcoded nurse list for MVP (all using test number for demo)
const NURSES = [
  { name: 'Nurse Sarah Johnson', phone: '+13854019951' },
  { name: 'Nurse Michael Chen', phone: '+13854019951' },
  { name: 'Nurse Emily Rodriguez', phone: '+13854019951' },
  { name: 'Dr. David Kim (On-Call)', phone: '+13854019951' },
];

interface ToastMessage {
  id: string;
  type: 'success' | 'error';
  message: string;
}

export default function ManualAlertsPanel() {
  const [selectedNurse, setSelectedNurse] = useState('');
  const [customMessage, setCustomMessage] = useState('');
  const [alertType, setAlertType] = useState<'sms' | 'call'>('call'); // Default to voice call
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
      const endpoint = alertType === 'call' ? '/alerts/call' : '/alerts/trigger';
      const response = await fetch(`${API_URL}${endpoint}`, {
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
      
      const alertTypeText = alertType === 'call' ? 'Voice call placed to' : 'SMS sent to';
      showToast('success', `✅ ${alertTypeText} ${NURSES.find(n => n.phone === selectedNurse)?.name}`);
      
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
      <div className="bg-surface border border-neutral-200">
        {/* Header */}
        <div className="px-5 py-4 border-b-2 border-neutral-950">
          <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
            Send Staff Alert
          </h2>
        </div>
        
        {/* Content */}
        <div className="p-5 space-y-4">
          {/* Nurse Selection */}
          <div>
            <label className="block text-xs font-light text-neutral-600 mb-2">
              Recipient
            </label>
            <select
              value={selectedNurse}
              onChange={(e) => setSelectedNurse(e.target.value)}
              className="w-full border border-neutral-200 px-3 py-2 text-sm focus:outline-none focus:border-primary-700 transition-colors bg-white"
              disabled={isSending}
            >
              <option value="">Select staff member...</option>
              {NURSES.map((nurse, index) => (
                <option key={`${nurse.name}-${index}`} value={nurse.phone}>
                  {nurse.name}
                </option>
              ))}
            </select>
          </div>

          {/* Alert Type */}
          <div>
            <label className="block text-xs font-light text-neutral-600 mb-2">
              Method
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setAlertType('call')}
                disabled={isSending}
                className={`flex-1 px-3 py-2 text-xs uppercase tracking-wider transition-all border
                  ${alertType === 'call'
                    ? 'bg-primary-700 text-white border-primary-700'
                    : 'bg-white text-neutral-600 border-neutral-200 hover:border-neutral-400'
                  } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                Voice
              </button>
              <button
                onClick={() => setAlertType('sms')}
                disabled={isSending}
                className={`flex-1 px-3 py-2 text-xs uppercase tracking-wider transition-all border
                  ${alertType === 'sms'
                    ? 'bg-primary-700 text-white border-primary-700'
                    : 'bg-white text-neutral-600 border-neutral-200 hover:border-neutral-400'
                  } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                SMS
              </button>
            </div>
          </div>

          {/* Message */}
          <div>
            <label className="block text-xs font-light text-neutral-600 mb-2">
              Message
            </label>
            <textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Alert message..."
              className="w-full border border-neutral-200 px-3 py-2 text-sm focus:outline-none focus:border-primary-700 transition-colors resize-none bg-white"
              rows={3}
              disabled={isSending}
              maxLength={160}
            />
            <p className="text-[10px] text-neutral-400 mt-1">
              {customMessage.length}/160
            </p>
          </div>

          {/* Send Button */}
          <button
            onClick={handleSendAlert}
            disabled={isSending || !selectedNurse || !customMessage.trim()}
            className={`w-full px-4 py-2 text-sm uppercase tracking-wider transition-all
              ${isSending || !selectedNurse || !customMessage.trim()
                ? 'bg-neutral-200 text-neutral-400 cursor-not-allowed border border-neutral-200'
                : 'bg-primary-700 text-white hover:bg-primary-800 border border-primary-700'
              }`}
          >
            {isSending ? 'Sending...' : 'Send Alert'}
          </button>
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
