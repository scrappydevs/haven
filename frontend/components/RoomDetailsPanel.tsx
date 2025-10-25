'use client';

import { motion } from 'framer-motion';

interface Room {
  id: string;
  name: string;
  type: 'patient' | 'nurse_station' | 'other';
  assignedPatient?: {
    patient_id: string;
    name: string;
    age: number;
    condition: string;
    photo_url: string;
  };
  assignedNurses?: Array<{
    id: string;
    name: string;
    shift: string;
  }>;
}

interface AvailablePatient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

interface RoomDetailsPanelProps {
  room: Room | null;
  onClose: () => void;
  onUnassignPatient: () => void;
  availablePatients: AvailablePatient[];
  onAssignPatient: (patient: AvailablePatient) => void;
  onGenerateReport?: (patientId: string, roomId: string) => void;
}

export default function RoomDetailsPanel({ room, onClose, onUnassignPatient, availablePatients, onAssignPatient, onGenerateReport }: RoomDetailsPanelProps) {
  if (!room) return null;

  const handleDownloadReport = async () => {
    if (!room.assignedPatient) return;
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reports/discharge/${room.assignedPatient.patient_id}/${room.id}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `discharge-report-${room.assignedPatient.patient_id}-${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Failed to generate report. Please try again.');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-surface border-l-2 border-neutral-950 p-6 h-full overflow-y-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b-2 border-neutral-950">
        <div>
          <h3 className="text-xl font-light tracking-tight text-neutral-950">{room.name}</h3>
          <p className="label-uppercase text-neutral-500 mt-1">
            {room.type.replace('_', ' ')}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-neutral-500 hover:text-neutral-950 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Patient Assignment */}
      {room.type === 'patient' && (
        <div className="mb-6">
          <h4 className="label-uppercase text-neutral-700 mb-4">Assigned Patient</h4>
          
          {room.assignedPatient ? (
            <div className="border border-neutral-200 p-4">
              <div className="flex items-start gap-3 mb-4">
                {room.assignedPatient.photo_url && room.assignedPatient.photo_url.trim() !== '' ? (
                  <img
                    src={room.assignedPatient.photo_url}
                    alt={room.assignedPatient.name}
                    className="w-16 h-16 object-cover border border-neutral-950"
                    onError={(e) => {
                      // Hide broken image and show initials instead
                      e.currentTarget.style.display = 'none';
                      const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                      if (fallback) fallback.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div 
                  className="w-16 h-16 border border-neutral-950 bg-primary-100 flex items-center justify-center"
                  style={{ display: (room.assignedPatient.photo_url && room.assignedPatient.photo_url.trim() !== '') ? 'none' : 'flex' }}
                >
                  <span className="text-xl font-light text-primary-700">
                    {room.assignedPatient.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                  </span>
                </div>
                <div className="flex-1">
                  <h5 className="font-light text-neutral-950 mb-1">
                    {room.assignedPatient.name}
                  </h5>
                  <p className="label-uppercase text-primary-700 mb-2">
                    {room.assignedPatient.patient_id}
                  </p>
                  {room.assignedPatient.age > 0 && (
                    <p className="text-xs text-neutral-500">
                      {room.assignedPatient.age}y/o
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-neutral-50 border border-neutral-200 p-3 mb-4">
                <p className="label-uppercase text-neutral-600 mb-2">Condition</p>
                <p className="text-sm font-light text-neutral-950">
                  {room.assignedPatient.condition}
                </p>
              </div>

              <div className="space-y-2">
                <button
                  onClick={handleDownloadReport}
                  className="w-full border border-primary-700 px-4 py-2 font-light text-xs uppercase tracking-wider text-primary-700 hover:bg-primary-700 hover:text-white transition-all flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  Generate Discharge Report
                </button>
                <button
                  onClick={onUnassignPatient}
                  className="w-full border border-accent-terra px-4 py-2 font-light text-xs uppercase tracking-wider text-accent-terra hover:bg-accent-terra hover:text-white transition-all"
                >
                  Remove from Room
                </button>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-xs font-light text-neutral-500 mb-3 pb-2 border-b border-neutral-200">
                Available Patients ({availablePatients.length})
              </p>
              {availablePatients.length === 0 ? (
                <div className="text-center py-6 text-neutral-400 text-xs">
                  No available patients
                </div>
              ) : (
                <div className="space-y-2">
                  {availablePatients.map((patient) => (
                    <div
                      key={patient.id}
                      className="flex items-center gap-3 p-2 hover:bg-neutral-50 transition-colors border-b border-neutral-100 last:border-b-0"
                    >
                      {patient.photo_url ? (
                        <img
                          src={patient.photo_url}
                          alt={patient.name}
                          className="w-10 h-10 object-cover border border-neutral-300"
                        />
                      ) : (
                        <div className="w-10 h-10 border border-neutral-300 bg-primary-100 flex items-center justify-center">
                          <span className="text-xs font-light text-primary-700">
                            {patient.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                          </span>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-light text-neutral-950 text-xs truncate">{patient.name}</p>
                        <p className="text-[10px] font-light text-neutral-500">
                          {patient.age}y/o • {patient.patient_id}
                        </p>
                      </div>
                      <button
                        onClick={() => onAssignPatient(patient)}
                        className="w-7 h-7 flex items-center justify-center border border-primary-700 text-primary-700 hover:bg-primary-700 hover:text-white transition-colors flex-shrink-0"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Nurse Station */}
      {room.type === 'nurse_station' && (
        <div>
          <h4 className="label-uppercase text-neutral-700 mb-4">Assigned Nurses</h4>
          
          {room.assignedNurses && room.assignedNurses.length > 0 ? (
            <div className="space-y-3">
              {room.assignedNurses.map(nurse => (
                <div key={nurse.id} className="border border-neutral-200 p-3 flex items-center justify-between">
                  <div>
                    <p className="font-light text-neutral-950 text-sm">{nurse.name}</p>
                    <p className="label-uppercase text-neutral-500 text-xs">{nurse.shift}</p>
                  </div>
                  <button
                    className="border border-neutral-300 px-3 py-1 font-light text-xs uppercase tracking-wider text-neutral-700 hover:border-accent-terra hover:text-accent-terra transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="border border-neutral-200 bg-neutral-50 p-6 text-center">
              <p className="text-sm font-light text-neutral-500 mb-4">
                No nurses assigned
              </p>
              <button
                className="border-2 border-primary-700 px-6 py-2 font-normal text-xs uppercase tracking-wider text-primary-700 hover:bg-primary-700 hover:text-white transition-all"
              >
                Assign Nurse
              </button>
            </div>
          )}
        </div>
      )}

      {/* Room Info */}
      <div className="mt-6 pt-6 border-t border-neutral-200">
        <h4 className="label-uppercase text-neutral-700 mb-4">Room Information</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="font-light text-neutral-500">Room ID:</span>
            <span className="font-light text-neutral-950">{room.id}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-light text-neutral-500">Type:</span>
            <span className="font-light text-neutral-950">
              {room.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="font-light text-neutral-500">Status:</span>
            <span className={`font-light ${
              room.assignedPatient ? 'text-primary-700' : 'text-neutral-400'
            }`}>
              {room.assignedPatient ? 'Occupied' : 'Available'}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

