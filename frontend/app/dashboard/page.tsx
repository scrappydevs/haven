'use client';

import { useEffect, useState, useCallback } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import InfoBar from '@/components/InfoBar';
import DetailPanel from '@/components/DetailPanel';
import StatsBar from '@/components/StatsBar';
import PatientSearchModal from '@/components/PatientSearchModal';

interface Patient {
  id: number;
  name: string;
  age: number;
  condition: string;
  baseline_vitals: {
    heart_rate: number;
  };
}

interface Alert {
  patient_id: number;
  message: string;
  crs_score: number;
  heart_rate: number;
  timestamp: string;
}

interface SupabasePatient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

export default function DashboardPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [selectedCvData, setSelectedCvData] = useState<any>(null);
  const [stats, setStats] = useState({
    patients_monitored: 47,
    active_alerts: 0,
    daily_cost_savings: 17550
  });

  // Box assignment system (which patient is in which box)
  const [boxAssignments, setBoxAssignments] = useState<(SupabasePatient | null)[]>([
    null, null, null, null, null, null  // 6 boxes, all empty initially
  ]);

  // Patient selection modal
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedBoxIndex, setSelectedBoxIndex] = useState<number | null>(null);
  const [activeStreams, setActiveStreams] = useState<string[]>([]);

  // Open patient selection for a specific box
  const openPatientSelectionForBox = async (boxIndex: number) => {
    setSelectedBoxIndex(boxIndex);

    // Fetch active streams
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/streams/active`);
      const data = await res.json();
      setActiveStreams(data.active_streams || []);
    } catch (error) {
      console.error('Error fetching active streams:', error);
    }

    setShowPatientModal(true);
  };

  // Assign patient to a box
  const assignPatientToBox = (patient: SupabasePatient) => {
    if (selectedBoxIndex === null) return;

    setBoxAssignments(prev => {
      const newAssignments = [...prev];
      newAssignments[selectedBoxIndex] = patient;  // Store full patient object
      return newAssignments;
    });

    setShowPatientModal(false);
    setSelectedPatientId(selectedBoxIndex);  // Auto-select the newly assigned box
    console.log(`✅ Assigned ${patient.patient_id} to box ${selectedBoxIndex}`);
  };

  // Stable callback for CV data updates
  const handleCvDataUpdate = useCallback((patientId: number, data: any) => {
    // Only update if this is the selected patient
    if (patientId === selectedPatientId) {
      setSelectedCvData(data);
    }
  }, [selectedPatientId]);

  useEffect(() => {
    // Fetch patients from backend
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients`)
      .then(res => res.json())
      .then(data => {
        setPatients(data);
        // Select first patient by default
        if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        }
      })
      .catch(err => console.error('Error fetching patients:', err));

    // Poll for alerts every 2 seconds
    const alertInterval = setInterval(() => {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/alerts`)
        .then(res => res.json())
        .then(data => setAlerts(data))
        .catch(err => console.error('Error fetching alerts:', err));
    }, 2000);

    // Fetch stats
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Error fetching stats:', err));

    return () => clearInterval(alertInterval);
  }, []);

  // No longer need displayedPatients - we use boxAssignments instead

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <span className="text-2xl">👁️</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">TrialSentinel AI</h1>
                <p className="text-sm text-slate-400">Linvoseltamab Phase III - NCT04649359</p>
              </div>
            </div>

            {/* Stats */}
            <StatsBar stats={stats} alertCount={alerts.length} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Video Grid (Left - 8 columns for larger videos) */}
          <div className="col-span-8">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">Patient Monitoring</h2>
              <p className="text-sm text-slate-400">Click any feed to view detailed analysis</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {boxAssignments.map((patient, boxIndex) => {
                // Empty box - show + button
                if (!patient) {
                  return (
                    <div key={boxIndex} className="flex flex-col">
                      <div className="relative rounded-t-lg overflow-hidden border-2 border-slate-700 bg-slate-900/50">
                        <div className="w-full aspect-video flex items-center justify-center">
                          <button
                            onClick={() => openPatientSelectionForBox(boxIndex)}
                            className="w-20 h-20 rounded-full bg-slate-800 hover:bg-blue-500 border-2 border-slate-600 hover:border-blue-400 text-slate-400 hover:text-white text-4xl transition-all duration-200 hover:scale-110"
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="bg-slate-800 border-2 border-t-0 border-slate-700 rounded-b-lg px-4 py-3">
                        <p className="text-sm text-slate-500 text-center">Box {boxIndex + 1} - Empty</p>
                      </div>
                    </div>
                  );
                }

                // Assigned box - show VideoPlayer with patient stream
                return (
                  <div key={boxIndex} className="flex flex-col">
                    <VideoPlayer
                      patient={{
                        id: boxIndex,
                        name: patient.name,
                        age: patient.age,
                        condition: patient.condition,
                        baseline_vitals: { heart_rate: 75 }
                      }}
                      isLive={true}
                      patientId={patient.patient_id}
                      isSelected={selectedPatientId === boxIndex}
                      onCvDataUpdate={handleCvDataUpdate}
                    />
                    <InfoBar
                      patientId={patient.patient_id}
                      patientName={patient.name}
                      isLive={true}
                      isSelected={selectedPatientId === boxIndex}
                      onClick={() => {
                        setSelectedPatientId(boxIndex);
                      }}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detail Panel (Right - 4 columns) */}
          <div className="col-span-4">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">Patient Details</h2>
              <p className="text-sm text-slate-400">
                {selectedPatientId !== null && boxAssignments[selectedPatientId]
                  ? `${boxAssignments[selectedPatientId]?.name} - Live Analysis`
                  : 'Select a patient to view details'}
              </p>
            </div>
            <DetailPanel
              patient={
                selectedPatientId !== null && boxAssignments[selectedPatientId]
                  ? {
                      id: selectedPatientId,
                      name: boxAssignments[selectedPatientId]!.name,
                      age: boxAssignments[selectedPatientId]!.age,
                      condition: boxAssignments[selectedPatientId]!.condition
                    }
                  : null
              }
              cvData={selectedCvData}
              isLive={true}
            />
          </div>
        </div>
      </div>

      {/* Patient Search Modal */}
      <PatientSearchModal
        isOpen={showPatientModal}
        onClose={() => setShowPatientModal(false)}
        onSelect={assignPatientToBox}
        activeStreams={activeStreams}
        assignedPatients={boxAssignments
          .filter((p): p is SupabasePatient => p !== null)
          .map(p => p.patient_id)}
        mode="assign-stream"
      />
    </div>
  );
}

