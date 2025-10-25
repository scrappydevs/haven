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
  const [patientEvents, setPatientEvents] = useState<Record<number, any[]>>({});  // Events per box
  const [stats, setStats] = useState({
    patients_monitored: 47,
    active_alerts: 0,
    daily_cost_savings: 17550
  });

  // Box assignment system (which patient is in which box)
  const [boxAssignments, setBoxAssignments] = useState<(SupabasePatient | null)[]>([
    null, null, null, null, null, null  // 6 boxes, all empty initially
  ]);

  // Monitoring conditions for each box
  const [boxMonitoringConditions, setBoxMonitoringConditions] = useState<Record<number, string[]>>({});

  // Patient selection modal (one-step flow)
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

  // Assign patient to box (reads monitoring config from localStorage set by Stream page)
  const assignPatientToBox = (patient: SupabasePatient) => {
    if (selectedBoxIndex === null) return;

    // Read monitoring config from localStorage (set by Stream page)
    const savedConditions = localStorage.getItem(`monitoring-${patient.patient_id}`);
    const conditions = savedConditions ? JSON.parse(savedConditions) : [];

    // Assign patient to box
    setBoxAssignments(prev => {
      const newAssignments = [...prev];
      newAssignments[selectedBoxIndex] = patient;
      return newAssignments;
    });

    // Store monitoring conditions for this box
    setBoxMonitoringConditions(prev => ({
      ...prev,
      [selectedBoxIndex]: conditions
    }));

    setShowPatientModal(false);
    setSelectedPatientId(selectedBoxIndex);  // Auto-select the newly assigned box

    // Add initial monitoring event
    const protocolsText = conditions.length > 0
      ? `Monitoring: ${conditions.join(', ')}`
      : 'No protocols configured (configure in Stream page)';

    addPatientEvent(selectedBoxIndex, {
      timestamp: new Date().toISOString(),
      type: 'system',
      severity: conditions.length > 0 ? 'info' : 'warning',
      message: '📹 Monitoring Started',
      details: `Assigned ${patient.name} to Box ${selectedBoxIndex + 1} - ${protocolsText}`
    });

    console.log(`✅ Assigned ${patient.patient_id} to box ${selectedBoxIndex} with conditions: ${conditions.length > 0 ? conditions.join(', ') : 'none'}`);
  };

  // Add event to patient's log
  const addPatientEvent = useCallback((boxIndex: number, event: any) => {
    setPatientEvents(prev => {
      const patientEventLog = prev[boxIndex] || [];
      // Keep last 20 events
      const newLog = [event, ...patientEventLog].slice(0, 20);
      return { ...prev, [boxIndex]: newLog };
    });
  }, []);

  // Stable callback for CV data updates with frequent logging
  const handleCvDataUpdate = useCallback((patientId: number, data: any) => {
    // Only update if this is the selected patient
    if (patientId === selectedPatientId) {
      const prevData = selectedCvData;
      setSelectedCvData(data);

      const metrics = data?.metrics || {};
      const prevMetrics = prevData?.metrics || {};

      // Log every frame update (real-time console style)
      const logEntries: any[] = [];

      // Critical alerts first
      if (metrics.alert && !prevMetrics.alert) {
        const triggers = metrics.alert_triggers || [];
        const triggerText = triggers.length > 0 ? triggers.join(', ') : 'Critical threshold exceeded';
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'alert',
          severity: 'high',
          message: '🚨 Alert Triggered',
          details: triggerText
        });
      }

      // CRS monitoring logs
      if (metrics.crs_score !== undefined) {
        if (metrics.crs_score > 0.7 && (!prevMetrics.crs_score || prevMetrics.crs_score <= 0.7)) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'threshold',
            severity: 'high',
            message: 'CRS Risk Elevated',
            details: `Score: ${(metrics.crs_score * 100).toFixed(1)}% [HIGH]`
          });
        }

        // Log periodic CRS readings
        if (Math.random() < 0.15 && metrics.crs_score > 0.3) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'monitoring',
            severity: 'info',
            message: 'CRS Analysis',
            details: `Facial flushing detected: ${(metrics.crs_score * 100).toFixed(1)}%`
          });
        }
      }

      // Heart rate monitoring
      if (metrics.heart_rate && prevMetrics.heart_rate) {
        const hrDiff = metrics.heart_rate - prevMetrics.heart_rate;
        if (Math.abs(hrDiff) > 3 || Math.random() < 0.1) {
          const trend = hrDiff > 0 ? '↑' : hrDiff < 0 ? '↓' : '→';
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'vital',
            severity: 'info',
            message: 'Heart Rate Update',
            details: `${metrics.heart_rate} bpm ${trend} (${hrDiff > 0 ? '+' : ''}${hrDiff})`
          });
        }
      }

      // Respiratory rate
      if (metrics.respiratory_rate && Math.random() < 0.08) {
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'vital',
          severity: 'info',
          message: 'Respiratory Analysis',
          details: `Rate: ${metrics.respiratory_rate} breaths/min`
        });
      }

      // Face touching behavior
      if (metrics.face_touching_frequency > 0) {
        if (metrics.face_touching_frequency > 5 && (!prevMetrics.face_touching_frequency || prevMetrics.face_touching_frequency <= 5)) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'behavior',
            severity: 'moderate',
            message: 'Behavior Alert',
            details: `Frequent face touching: ${metrics.face_touching_frequency}/min`
          });
        } else if (Math.random() < 0.12 && metrics.face_touching_frequency > 2) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'behavior',
            severity: 'info',
            message: 'Face Touching Detected',
            details: `Count: ${metrics.face_touching_frequency} touches/min`
          });
        }
      }

      // Restlessness monitoring
      if (metrics.restlessness_index > 0.5 && Math.random() < 0.1) {
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'behavior',
          severity: metrics.restlessness_index > 0.7 ? 'moderate' : 'info',
          message: 'Movement Analysis',
          details: `Restlessness: ${(metrics.restlessness_index * 100).toFixed(0)}%`
        });
      }

      // Tremor detection
      if (metrics.tremor_detected && !prevMetrics.tremor_detected) {
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'seizure',
          severity: 'high',
          message: 'Tremor Detected',
          details: `Magnitude: ${metrics.tremor_magnitude?.toFixed(2)} [SEIZURE RISK]`
        });
      }

      // Movement patterns
      if (metrics.movement_vigor > 1.0 && Math.random() < 0.08) {
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'monitoring',
          severity: 'info',
          message: 'Movement Tracking',
          details: `Vigor index: ${metrics.movement_vigor?.toFixed(2)}`
        });
      }

      // Add all logs
      logEntries.forEach(entry => addPatientEvent(patientId, entry));
    }
  }, [selectedPatientId, selectedCvData, addPatientEvent]);

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
                      monitoringConditions={boxMonitoringConditions[boxIndex] || []}
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
              monitoringConditions={selectedPatientId !== null ? (boxMonitoringConditions[selectedPatientId] || []) : []}
              events={selectedPatientId !== null ? (patientEvents[selectedPatientId] || []) : []}
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

