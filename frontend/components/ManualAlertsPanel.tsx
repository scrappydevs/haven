'use client';

import { useState, useEffect, useRef } from 'react';
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

interface ManualAlertsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ManualAlertsPanel({ isOpen, onClose }: ManualAlertsPanelProps) {
  const [selectedNurse, setSelectedNurse] = useState('');
  const [customMessage, setCustomMessage] = useState('');
  const [alertType, setAlertType] = useState<'sms' | 'call'>('call'); // Default to voice call
  const [isSending, setIsSending] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isDropdownOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  useEffect(() => {
    if (!isOpen) {
      setIsDropdownOpen(false);
    }
  }, [isOpen]);

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

  const showToast = (type: 'success' | 'error', message: string) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, type, message }]);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  const selectedNurseInfo = NURSES.find(n => n.phone === selectedNurse);

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
      showToast('success', `✅ ${alertTypeText} ${selectedNurseInfo?.name ?? 'recipient'}`);
      
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
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-neutral-950/30 backdrop-blur-[2px]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
            />
            <motion.div
              className="fixed inset-0 z-50 flex justify-end sm:justify-center items-start sm:items-center pt-24 sm:pt-0 pr-6 sm:pr-0"
              initial={{ opacity: 0, y: -16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
            >
              <div className="w-full max-w-md bg-white border border-neutral-200 rounded-3xl shadow-2xl overflow-hidden">
                <div className="flex items-start justify-between px-6 py-5 border-b border-neutral-200">
                  <div>
                    <h2 className="text-lg font-medium uppercase tracking-wider text-neutral-950">
            Manual Alerts
          </h2>
                    <p className="text-xs text-neutral-500 font-light mt-1">
                      Reach nursing staff instantly when you need support.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={onClose}
                    className="p-2 rounded-full border border-transparent text-neutral-400 hover:text-neutral-700 hover:border-neutral-200 transition-colors"
                    aria-label="Close manual alerts"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                  </button>
        </div>

                <div className="px-6 py-6">
        {/* Nurse Selection */}
                  <div className="mb-5">
          <label className="block text-xs font-medium uppercase tracking-wider text-neutral-700 mb-2">
            Select Recipient
          </label>
                    <div ref={dropdownRef} className="relative">
                      <button
                        type="button"
                        onClick={() => !isSending && setIsDropdownOpen(prev => !prev)}
            disabled={isSending}
                        className={`w-full px-4 py-3 border border-neutral-300 rounded-full text-sm flex items-center justify-between gap-3 transition-colors bg-white ${
                          isSending ? 'opacity-50 cursor-not-allowed' : 'hover:border-neutral-950'
                        }`}
                      >
                        <span className={selectedNurseInfo ? 'text-neutral-900' : 'text-neutral-400'}>
                          {selectedNurseInfo ? selectedNurseInfo.name : 'Choose a nurse...'}
                        </span>
                        <svg
                          className={`w-4 h-4 text-neutral-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
                          viewBox="0 0 16 16"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </button>
                      <AnimatePresence>
                        {isDropdownOpen && (
                          <motion.div
                            initial={{ opacity: 0, y: -8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -8 }}
                            className="absolute z-50 mt-2 w-full bg-white border border-neutral-200 rounded-2xl shadow-xl overflow-hidden"
                          >
                            {NURSES.map((nurse, index) => (
                              <button
                                type="button"
                                key={`${nurse.name}-${index}`}
                                onClick={() => {
                                  setSelectedNurse(nurse.phone);
                                  setIsDropdownOpen(false);
                                }}
                                className="w-full px-4 py-3 text-left text-sm hover:bg-neutral-50 transition-colors"
                              >
                                <span className="block font-medium text-neutral-900">{nurse.name}</span>
                                <span className="text-xs text-neutral-500">{nurse.phone}</span>
                              </button>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Alert Type Toggle */}
                  <div className="mb-5">
                    <label className="block text-xs font-medium uppercase tracking-wider text-neutral-700 mb-2">
                      Alert Type
                    </label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setAlertType('call')}
                        disabled={isSending}
                        className={`flex-1 px-4 py-2 text-sm font-semibold uppercase tracking-wide rounded-full transition-all ${
                          alertType === 'call'
                            ? 'bg-neutral-950 text-white shadow-sm'
                            : 'bg-white text-neutral-700'
                        } ${isSending ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white hover:text-neutral-950'}`}
                      >
                        Voice Call (TTS)
                      </button>
                      <button
                        type="button"
                        onClick={() => setAlertType('sms')}
                        disabled={isSending}
                        className={`flex-1 px-4 py-2 text-sm font-semibold uppercase tracking-wide rounded-full transition-all ${
                          alertType === 'sms'
                            ? 'bg-neutral-950 text-white shadow-sm'
                            : 'bg-white text-neutral-700'
                        } ${isSending ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white hover:text-neutral-950'}`}
                      >
                        SMS Text
                      </button>
                    </div>
                    <p className="text-xs text-neutral-500 mt-2 font-light">
                      {alertType === 'call'
                        ? 'AI voice will read your message aloud - no 10DLC needed!'
                        : 'SMS requires 10DLC registration (1-2 days) - use Voice for immediate alerts.'}
                    </p>
        </div>

        {/* Message Input */}
                  <div className="mb-5">
          <label className="block text-xs font-medium uppercase tracking-wider text-neutral-700 mb-2">
            Message
          </label>
          <textarea
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="Enter alert message (e.g., Patient P-001 showing elevated CRS score...)"
                      className="w-full border border-neutral-300 px-4 py-3 text-sm focus:outline-none focus:border-neutral-950 transition-colors resize-none bg-white rounded-2xl"
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
                    className={`w-full px-6 py-3 text-sm font-semibold uppercase tracking-wider rounded-full transition-all ${
                      isSending || !selectedNurse || !customMessage.trim()
              ? 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
                        : 'bg-neutral-950 text-white hover:bg-neutral-800 shadow-sm'
            }`}
        >
          {isSending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
                        {alertType === 'call' ? 'Placing Call...' : 'Sending SMS...'}
            </span>
          ) : (
                      alertType === 'call' ? 'Place Voice Call' : 'Send SMS'
          )}
        </button>

        {/* Info Notice */}
                  <div className="mt-5 p-4 bg-neutral-50 border border-neutral-200 rounded-2xl">
          <p className="text-xs text-neutral-600 font-light">
                      <span className="font-medium">Note:</span>{' '}
                      {alertType === 'call'
                        ? 'Voice calls work immediately with TTS - no carrier restrictions.'
                        : 'SMS requires 10DLC registration (pending). Use Voice for immediate alerts.'}
                      {' '}In production, alerts will trigger automatically when anomalies are detected.
          </p>
        </div>
      </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-[60] space-y-2">
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
