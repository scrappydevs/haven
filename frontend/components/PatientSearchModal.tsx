'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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
  activeStreams: string[];  // List of patient_ids currently streaming
  assignedPatients?: string[];  // List of patient_ids already assigned to boxes (optional)
  mode?: 'start-stream' | 'assign-stream';  // Mode: start-stream = select to start streaming, assign-stream = select from active streams
}

export default function PatientSearchModal({ isOpen, onClose, onSelect, activeStreams, assignedPatients = [], mode = 'start-stream' }: PatientSearchModalProps) {
  const [search, setSearch] = useState('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch patients based on search query
  useEffect(() => {
    if (!isOpen) return;

    const fetchPatients = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients/search?q=${search}`);
        const data = await res.json();
        setPatients(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching patients:', error);
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
          className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative bg-slate-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden border border-slate-700"
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-white">
                {mode === 'assign-stream' ? 'Assign Active Stream to Box' : 'Select Patient to Stream'}
              </h2>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
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
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
                autoFocus
              />
              {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
          </div>

          {/* Patient Grid */}
          <div className="p-6 overflow-y-auto max-h-[calc(80vh-180px)]">
            {availablePatients.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-400 text-lg">
                  {mode === 'assign-stream'
                    ? (activeStreams.length === 0
                        ? 'No active streams available'
                        : 'All active streams are already assigned')
                    : (search ? 'No patients found' : 'Start typing to search patients')}
                </p>
                {mode === 'assign-stream' && activeStreams.length > 0 && (
                  <p className="text-slate-500 text-sm mt-2">
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
                    className="flex items-start gap-4 p-4 bg-slate-900/50 hover:bg-slate-900 border border-slate-700 hover:border-blue-500 rounded-lg transition-all text-left group"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {/* Avatar */}
                    <img
                      src={patient.photo_url}
                      alt={patient.name}
                      className="w-16 h-16 rounded-full object-cover border-2 border-slate-600 group-hover:border-blue-500 transition-colors"
                    />

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="font-semibold text-white text-lg truncate">
                          {patient.name}
                        </h3>
                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full whitespace-nowrap">
                          {patient.patient_id}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mb-2">
                        {patient.age}y/o • {patient.gender}
                      </p>
                      <p className="text-sm text-slate-300 line-clamp-2">
                        {patient.condition}
                      </p>
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-700 bg-slate-900/50">
            <p className="text-sm text-slate-400 text-center">
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
