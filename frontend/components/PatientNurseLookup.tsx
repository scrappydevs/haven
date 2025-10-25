'use client';

import { useState, useEffect } from 'react';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  condition: string;
  photo_url?: string;
  enrollment_status?: string;
}

export default function PatientManagement() {
  const [allPatients, setAllPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'monitoring'>('all');

  // Fetch all patients on mount
  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    setIsLoading(true);
    try {
      // Use the same endpoint as the rest of the codebase
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients/search?q=`);
      const data = await response.json();
      console.log('📦 Fetched patients:', data);
      console.log('📦 Is array:', Array.isArray(data));
      console.log('📦 Length:', data?.length);
      
      // Handle response - should be array directly
      const patientList = Array.isArray(data) ? data : [];
      
      console.log(`✅ Loaded ${patientList.length} total patients`);
      setAllPatients(patientList);
    } catch (error) {
      console.error('❌ Error fetching patients:', error);
      setAllPatients([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter patients based on current filter
  const getFilteredPatients = () => {
    if (filterStatus === 'active') {
      return allPatients.filter((p: Patient) => p.enrollment_status === 'active');
    } else if (filterStatus === 'monitoring') {
      // For now, return all (room assignment filtering would need async call)
      return allPatients;
    }
    return allPatients; // 'all'
  };

  const filteredPatients = getFilteredPatients();

  return (
    <div className="bg-surface border border-neutral-200 flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b-2 border-neutral-950">
        <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
          Patient Management
        </h2>
      </div>

      {/* Filter Tabs */}
      <div className="px-6 py-3 border-b border-neutral-200 flex gap-4">
        <button
          onClick={() => setFilterStatus('all')}
          className={`px-3 py-1.5 text-xs font-light transition-colors ${
            filterStatus === 'all'
              ? 'text-neutral-950 border-b-2 border-primary-700'
              : 'text-neutral-500 hover:text-neutral-950'
          }`}
        >
          All ({allPatients.length})
        </button>
        <button
          onClick={() => setFilterStatus('active')}
          className={`px-3 py-1.5 text-xs font-light transition-colors ${
            filterStatus === 'active'
              ? 'text-neutral-950 border-b-2 border-primary-700'
              : 'text-neutral-500 hover:text-neutral-950'
          }`}
        >
          Active
        </button>
        <button
          onClick={() => setFilterStatus('monitoring')}
          className={`px-3 py-1.5 text-xs font-light transition-colors ${
            filterStatus === 'monitoring'
              ? 'text-neutral-950 border-b-2 border-primary-700'
              : 'text-neutral-500 hover:text-neutral-950'
          }`}
        >
          In Rooms
        </button>
      </div>

      {/* Patient List */}
      <div className="flex-1 overflow-y-auto relative">
        {isLoading ? (
          <div className="flex items-center justify-center h-full p-6">
            <div className="flex items-center gap-2 text-neutral-500">
              <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="text-sm font-light">Loading patients...</span>
            </div>
          </div>
        ) : selectedPatient ? (
          // Patient Details View
          <div className="p-6">
            <button
              onClick={() => setSelectedPatient(null)}
              className="flex items-center gap-2 text-neutral-500 hover:text-neutral-950 transition-colors mb-4"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              <span className="text-xs uppercase tracking-wider">Back to list</span>
            </button>

            <div className="border border-neutral-200 p-5">
              <div className="flex items-start gap-4 mb-5">
                {selectedPatient.photo_url ? (
                  <img
                    src={selectedPatient.photo_url}
                    alt={selectedPatient.name}
                    className="w-20 h-20 object-cover border border-neutral-950"
                  />
                ) : (
                  <div className="w-20 h-20 border border-neutral-950 bg-primary-100 flex items-center justify-center">
                    <span className="text-2xl font-light text-primary-700">
                      {selectedPatient.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                    </span>
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-lg font-light text-neutral-950 mb-1">
                    {selectedPatient.name}
                  </h3>
                  <p className="text-xs uppercase tracking-wider text-primary-700 mb-2">
                    {selectedPatient.patient_id}
                  </p>
                  <div className="flex gap-3 text-xs text-neutral-600">
                    <span>{selectedPatient.age}y/o</span>
                    <span>•</span>
                    <span>{selectedPatient.gender}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="border-t border-neutral-200 pt-3">
                  <p className="text-[10px] uppercase tracking-wider text-neutral-500 mb-1">Condition</p>
                  <p className="text-sm font-light text-neutral-950">{selectedPatient.condition}</p>
                </div>
                {selectedPatient.enrollment_status && (
                  <div className="border-t border-neutral-200 pt-3">
                    <p className="text-[10px] uppercase tracking-wider text-neutral-500 mb-1">Status</p>
                    <p className="text-sm font-light text-neutral-950 capitalize">{selectedPatient.enrollment_status}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : filteredPatients.length > 0 ? (
          // Patient List with sticky footer
          <>
            {/* Scrollable list with padding for footer */}
            <div className="overflow-y-auto h-full pb-10">
              {filteredPatients.map((patient) => (
                <button
                  key={patient.id}
                  onClick={() => setSelectedPatient(patient)}
                  className="w-full text-left px-6 py-4 border-b border-neutral-100 hover:bg-neutral-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {patient.photo_url ? (
                      <img
                        src={patient.photo_url}
                        alt={patient.name}
                        className="w-12 h-12 object-cover border border-neutral-300"
                      />
                    ) : (
                      <div className="w-12 h-12 border border-neutral-300 bg-primary-100 flex items-center justify-center">
                        <span className="text-sm font-light text-primary-700">
                          {patient.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                        </span>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-light text-neutral-950 mb-0.5 truncate">{patient.name}</p>
                      <div className="flex items-center gap-2 text-xs text-neutral-500">
                        <span>{patient.patient_id}</span>
                        <span>•</span>
                        <span>{patient.age}y/o</span>
                      </div>
                    </div>
                    <svg className="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
            
            {/* Sticky footer with count */}
            <div className="absolute bottom-0 left-0 right-0 px-6 py-3 bg-white border-t border-neutral-200 z-10">
              <p className="text-xs font-light text-neutral-500 text-center">
                {filteredPatients.length} {filteredPatients.length === 1 ? 'patient' : 'patients'}
              </p>
            </div>
          </>
        ) : (
          // Empty State
          <div className="flex items-center justify-center h-full p-6">
            <div className="text-center text-neutral-400">
              <p className="text-sm font-light">No patients in this category</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

