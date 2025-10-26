'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
  enrollment_status: string;
}

interface PatientSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (patient: Patient) => void;
  activeStreams: string[];  // List of patient_ids currently streaming (will be refreshed internally)
  assignedPatients?: string[];  // List of patient_ids already assigned to boxes (optional)
  mode?: 'start-stream' | 'assign-stream';  // Mode: start-stream = select to start streaming, assign-stream = select from active streams
}

export default function PatientSearchModal({ isOpen, onClose, onSelect, activeStreams: initialActiveStreams, assignedPatients = [], mode = 'start-stream' }: PatientSearchModalProps) {
  const [search, setSearch] = useState('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeStreams, setActiveStreams] = useState<string[]>(initialActiveStreams);

  // Auto-refresh active streams when modal opens
  useEffect(() => {
    if (!isOpen) return;

    const fetchActiveStreams = async () => {
      try {
        const apiUrl = getApiUrl();
        const res = await fetch(`${apiUrl}/streams/active`);
        const data = await res.json();
        const freshStreams = data.active_streams || [];
        console.log('🔄 Refreshed active streams:', freshStreams);
        setActiveStreams(freshStreams);
      } catch (error) {
        console.error('❌ Error refreshing active streams:', error);
        // Keep using the initial/existing activeStreams if fetch fails
      }
    };

    fetchActiveStreams();
  }, [isOpen]);

  // Fetch patients based on search query
  useEffect(() => {
    if (!isOpen) return;

    const fetchPatients = async () => {
      setLoading(true);
      try {
        const apiUrl = getApiUrl();
        const res = await fetch(`${apiUrl}/patients/search?q=${search}`);
        const data = await res.json();
        console.log('📦 Received data:', data);

        if (Array.isArray(data)) {
          console.log(`✅ Found ${data.length} patients`);
          setPatients(data);
        } else {
          console.warn('⚠️ Response is not an array:', data);
          setPatients([]);
        }
      } catch (error) {
        console.error('❌ Error fetching patients:', error);
        setPatients([]);
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeout = setTimeout(fetchPatients, 300);
    return () => clearTimeout(timeout);
  }, [search, isOpen]);

  // Filter based on mode
  const availablePatients = patients.filter(p => {
    if (mode === 'assign-stream') {
      // Dashboard mode: Show only patients who ARE streaming but NOT yet assigned to a box
      return activeStreams.includes(p.patient_id) && !assignedPatients.includes(p.patient_id);
    } else {
      // Stream page mode: Show only patients who are NOT currently streaming
      return !activeStreams.includes(p.patient_id);
    }
  });

  const handleSelect = (patient: Patient) => {
    onSelect(patient);
    onClose();
    setSearch('');
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-neutral-950/40"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.98, y: 20 }}
          className="relative bg-surface border border-neutral-200 max-w-2xl w-full max-h-[80vh] overflow-hidden rounded-lg"
        >
          {/* Header */}
          <div className="p-8 border-b border-neutral-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-light tracking-tight text-neutral-950">
                {mode === 'assign-stream' ? 'ASSIGN ACTIVE STREAM' : 'SELECT PATIENT TO STREAM'}
              </h2>
              <button
                onClick={onClose}
                className="text-neutral-500 hover:text-neutral-950 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Search Input */}
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search patients by name..."
                className="w-full bg-white border border-neutral-200 px-4 py-3 font-light text-sm text-neutral-950 placeholder:text-neutral-400 focus:outline-none focus:border-primary-700 transition-all"
                autoFocus
              />
              {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-5 h-5 border-2 border-primary-700 border-t-transparent animate-spin" />
                </div>
              )}
            </div>
          </div>

          {/* Patient Grid */}
          <div className="p-8 overflow-y-auto max-h-[calc(80vh-220px)]">
            {availablePatients.length === 0 ? (
              <div className="text-center py-16 border border-neutral-200 bg-neutral-50">
                <p className="text-neutral-500 text-base font-light">
                  {mode === 'assign-stream'
                    ? (activeStreams.length === 0
                        ? 'No active streams available'
                        : 'All active streams are already assigned')
                    : (search ? 'No patients found' : 'Start typing to search patients')}
                </p>
                {mode === 'assign-stream' && activeStreams.length > 0 && (
                  <p className="text-neutral-400 text-sm font-light mt-2">
                    {activeStreams.length} active stream(s), {assignedPatients.length} assigned
                  </p>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availablePatients.map((patient) => (
                  <motion.button
                    key={patient.id}
                    onClick={() => handleSelect(patient)}
                    className="flex items-start gap-4 p-5 bg-surface hover:bg-neutral-50 border border-neutral-200 hover:border-primary-700 transition-all text-left group"
                    whileHover={{ x: 2 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    {/* Avatar */}
                    <img
                      src={patient.photo_url}
                      alt={patient.name}
                      className="w-16 h-16 object-cover rounded-lg"
                    />

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="font-light text-neutral-950 text-base truncate">
                          {patient.name}
                        </h3>
                        <span className="bg-primary-100 text-primary-700 px-2 py-1 whitespace-nowrap rounded text-sm">
                          {patient.patient_id}
                        </span>
                      </div>
                      <p className="text-xs font-light text-neutral-500 mb-2">
                        {patient.age}y/o • {patient.gender}
                      </p>
                      <p className="text-sm font-light text-neutral-700 line-clamp-2">
                        {patient.condition}
                      </p>
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-neutral-200 bg-neutral-50">
            <p className="text-sm font-light text-neutral-500 text-center">
              {mode === 'assign-stream'
                ? 'Select an active stream to assign to this box'
                : 'Select a patient to start streaming from this device'}
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
