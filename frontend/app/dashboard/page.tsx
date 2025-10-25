'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import InfoBar from '@/components/InfoBar';
import DetailPanel from '@/components/DetailPanel';
import StatsBar from '@/components/StatsBar';
import PatientSearchModal from '@/components/PatientSearchModal';
import GlobalActivityFeed from '@/components/GlobalActivityFeed';

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

interface GlobalEvent {
  timestamp: string;
  patientId: number;
  patientName: string;
  type: string;
  severity: string;
  message: string;
  details: string;
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

  // View mode: overview (6 boxes + global feed) vs detail (1 large video + detail panel)
  const [viewMode, setViewMode] = useState<'overview' | 'detail'>('overview');

  // Global event feed for overview mode (consolidated from all patients)
  const [globalEventFeed, setGlobalEventFeed] = useState<GlobalEvent[]>([]);

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

  // Add event to global feed (for overview mode)
  const addGlobalEvent = useCallback((event: GlobalEvent) => {
    setGlobalEventFeed(prev => [event, ...prev].slice(0, 100)); // Keep last 100 events
  }, []);

  // Navigation between modes
  const onPatientClicked = (boxIndex: number) => {
    setSelectedPatientId(boxIndex);
    setViewMode('detail');
  };

  const onBackToOverview = () => {
    setViewMode('overview');
    // Keep selected patient ID so CV data still updates
  };

  // Throttle logging to reduce state updates (ref-based, no re-renders)
  const lastLogTime = useRef<number>(0);
  const LOG_THROTTLE_MS = 200; // Log at most 5 times per second instead of 30

  // Stable callback for CV data updates with throttled logging
  const handleCvDataUpdate = useCallback((patientId: number, data: any) => {
    // Only update if this is the selected patient
    if (patientId === selectedPatientId) {
      const prevData = selectedCvData;
      setSelectedCvData(data);

      const metrics = data?.metrics || {};
      const prevMetrics = prevData?.metrics || {};

      // Throttle log generation to reduce React state updates
      const now = Date.now();
      const shouldLog = now - lastLogTime.current >= LOG_THROTTLE_MS;
      if (!shouldLog && !metrics.alert) {
        // Skip logging unless it's an alert (always log alerts)
        return;
      }
      lastLogTime.current = now;

      // Log every 200ms (5 FPS) instead of every frame (30 FPS)
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

        // Log periodic CRS readings (reduced frequency due to throttling)
        if (Math.random() < 0.3 && metrics.crs_score > 0.3) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'monitoring',
            severity: 'info',
            message: 'CRS Analysis',
            details: `Facial flushing detected: ${(metrics.crs_score * 100).toFixed(1)}%`
          });
        }
      }

      // Heart rate monitoring (only log significant changes)
      if (metrics.heart_rate && prevMetrics.heart_rate) {
        const hrDiff = metrics.heart_rate - prevMetrics.heart_rate;
        if (Math.abs(hrDiff) > 5) {  // Increased threshold from 3 to 5
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

      // Respiratory rate (reduced frequency due to throttling)
      if (metrics.respiratory_rate && Math.random() < 0.15) {
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
        } else if (Math.random() < 0.25 && metrics.face_touching_frequency > 2) {
          logEntries.push({
            timestamp: new Date().toISOString(),
            type: 'behavior',
            severity: 'info',
            message: 'Face Touching Detected',
            details: `Count: ${metrics.face_touching_frequency} touches/min`
          });
        }
      }

      // Restlessness monitoring (reduced frequency due to throttling)
      if (metrics.restlessness_index > 0.5 && Math.random() < 0.2) {
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

      // Movement patterns (reduced frequency due to throttling)
      if (metrics.movement_vigor > 1.0 && Math.random() < 0.15) {
        logEntries.push({
          timestamp: new Date().toISOString(),
          type: 'monitoring',
          severity: 'info',
          message: 'Movement Tracking',
          details: `Vigor index: ${metrics.movement_vigor?.toFixed(2)}`
        });
      }

      // Add all logs to patient-specific and global feeds
      logEntries.forEach(entry => {
        // Add to patient log
        addPatientEvent(patientId, entry);

        // Add to global feed with patient info
        const patient = boxAssignments[patientId];
        if (patient) {
          addGlobalEvent({
            ...entry,
            patientId,
            patientName: patient.name
          });
        }
      });
    }
  }, [selectedPatientId, selectedCvData, addPatientEvent, addGlobalEvent, boxAssignments]);

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
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-2 border-neutral-950 bg-surface">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-4">
              <div>
                <h1 className="text-2xl font-playfair font-black bg-gradient-to-r from-primary-950 to-primary-700 bg-clip-text text-transparent">
                  TrialSentinel
                </h1>
                <p className="text-xs label-uppercase text-neutral-500 mt-1">Linvoseltamab Phase III - NCT04649359</p>
              </div>
            </div>

            {/* Stats */}
            <StatsBar stats={stats} alertCount={alerts.length} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        {viewMode === 'overview' ? (
          // OVERVIEW MODE: 6-box grid + global activity feed
          <div className="grid grid-cols-12 gap-6">
            {/* Video Grid (Left - 8 columns) */}
            <div className="col-span-8">
              <div className="mb-6">
                <h2 className="text-2xl font-light tracking-tight text-neutral-950 border-b-2 border-neutral-950 pb-2 inline-block">PATIENT MONITORING</h2>
                <p className="text-sm font-light text-neutral-500 mt-3">Click any feed to view detailed analysis</p>
              </div>

              <div className="grid grid-cols-3 gap-4">
              {boxAssignments.map((patient, boxIndex) => {
                // Empty box - show + button
                if (!patient) {
                  return (
                    <div key={boxIndex} className="flex flex-col">
                      <div className="relative overflow-hidden border border-neutral-200 bg-neutral-50">
                        <div className="w-full aspect-video flex items-center justify-center">
                          <button
                            onClick={() => openPatientSelectionForBox(boxIndex)}
                            className="w-16 h-16 bg-surface hover:bg-primary-700 border-2 border-neutral-300 hover:border-primary-700 text-neutral-400 hover:text-white text-3xl transition-all hover:scale-105 font-light"
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="bg-surface border border-neutral-200 border-t-0 px-4 py-3">
                        <p className="label-uppercase text-neutral-400 text-center">Box {boxIndex + 1} - Empty</p>
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
                        onPatientClicked(boxIndex);
                      }}
                    />
                  </div>
                );
              })}
            </div>
          </div>

            {/* Global Activity Feed (Right - 4 columns) */}
            <div className="col-span-4">
              <GlobalActivityFeed
                events={globalEventFeed}
                alerts={alerts}
                onPatientClick={onPatientClicked}
              />
            </div>
          </div>
        ) : (
          // DETAIL MODE: Large video + detail panel
          <div>
            {/* Back Button */}
            <div className="mb-4">
              <button
                onClick={onBackToOverview}
                className="flex items-center gap-2 border border-neutral-300 px-6 py-2 font-light text-xs uppercase tracking-wider text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Overview
              </button>
            </div>

            <div className="grid grid-cols-12 gap-6">
              {/* Large Video (Left - 8 columns) */}
              <div className="col-span-8">
                {selectedPatientId !== null && boxAssignments[selectedPatientId] && (
                  <div className="h-[calc(100vh-250px)]">
                    <VideoPlayer
                      patient={{
                        id: selectedPatientId,
                        name: boxAssignments[selectedPatientId]!.name,
                        age: boxAssignments[selectedPatientId]!.age,
                        condition: boxAssignments[selectedPatientId]!.condition,
                        baseline_vitals: { heart_rate: 75 }
                      }}
                      isLive={true}
                      patientId={boxAssignments[selectedPatientId]!.patient_id}
                      isSelected={true}
                      onCvDataUpdate={handleCvDataUpdate}
                      monitoringConditions={boxMonitoringConditions[selectedPatientId] || []}
                      fullscreenMode={true}
                    />
                  </div>
                )}
              </div>

              {/* Detail Panel (Right - 4 columns) */}
              <div className="col-span-4">
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
        )}
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

