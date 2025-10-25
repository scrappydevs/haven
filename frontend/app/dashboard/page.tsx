'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import InfoBar from '@/components/InfoBar';
import DetailPanel from '@/components/DetailPanel';
import StatsBar from '@/components/StatsBar';
import PatientSearchModal from '@/components/PatientSearchModal';
import GlobalActivityFeed from '@/components/GlobalActivityFeed';
import ManualAlertsPanel from '@/components/ManualAlertsPanel';
import PatientManagement from '@/components/PatientNurseLookup';
import { getApiUrl } from '@/lib/api';

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
  id?: string;
  alert_type: string;
  severity: string;
  patient_id?: string;
  room_id?: string;
  title: string;
  description?: string;
  status: string;
  triggered_at: string;
  metadata?: any;
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
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(true);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [selectedCvData, setSelectedCvData] = useState<any>(null);
  const [patientEvents, setPatientEvents] = useState<Record<number, any[]>>({});  // Events per box
  const [stats, setStats] = useState({
    patients_monitored: 47,
    active_alerts: 0
  });

  // View mode: overview (6 boxes + global feed) vs detail (1 large video + detail panel)
  const [viewMode, setViewMode] = useState<'overview' | 'detail'>('overview');

  // Global event feed for overview mode (consolidated from all patients)
  const [globalEventFeed, setGlobalEventFeed] = useState<GlobalEvent[]>([]);

  // Box assignment system (which patient is in which box)
  // Start with just one empty box, add more as patients are assigned
  const [boxAssignments, setBoxAssignments] = useState<(SupabasePatient | null)[]>([
    null  // Start with one empty box
  ]);

  // Monitoring conditions for each box
  const [boxMonitoringConditions, setBoxMonitoringConditions] = useState<Record<number, string[]>>({});

  // Monitoring levels for each box (BASELINE, ENHANCED, CRITICAL)
  const [boxMonitoringLevels, setBoxMonitoringLevels] = useState<Record<number, 'BASELINE' | 'ENHANCED' | 'CRITICAL'>>({});

  // Monitoring expiration times
  const [boxMonitoringExpires, setBoxMonitoringExpires] = useState<Record<number, string | null>>({});

  // Enabled metrics per box
  const [boxEnabledMetrics, setBoxEnabledMetrics] = useState<Record<number, string[]>>({});

  // Agent analyzing state
  const [boxAgentAnalyzing, setBoxAgentAnalyzing] = useState<Record<number, boolean>>({});

  // Last agent decision per box
  const [boxLastDecision, setBoxLastDecision] = useState<Record<number, {
    timestamp: Date;
    action: string;
    reason: string;
    confidence: number;
  } | null>>({});

  // Agent stats per box
  const [boxAgentStats, setBoxAgentStats] = useState<Record<number, {
    decisionsToday: number;
    escalationsToday: number;
  }>>({});

  const [isManualAlertsOpen, setManualAlertsOpen] = useState(false);


  // Patient selection modal (one-step flow)
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedBoxIndex, setSelectedBoxIndex] = useState<number | null>(null);
  const [activeStreams, setActiveStreams] = useState<string[]>([]);

  // Open patient selection for a specific box
  const openPatientSelectionForBox = async (boxIndex: number) => {
    setSelectedBoxIndex(boxIndex);

    // Fetch active streams
    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/streams/active`);
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

    // Assign patient to box and add a new empty box
    setBoxAssignments(prev => {
      const newAssignments = [...prev];
      newAssignments[selectedBoxIndex] = patient;
      // Add a new empty box at the end
      newAssignments.push(null);
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
      message: 'Monitoring Started',
      details: `Assigned ${patient.name} - ${protocolsText}`
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

  // Handle agent messages (monitoring state changes and alerts)
  const handleAgentMessage = useCallback((boxIndex: number, message: any) => {
    if (message.type === 'monitoring_state_change') {
      // Update monitoring level for this box
      setBoxMonitoringLevels(prev => ({
        ...prev,
        [boxIndex]: message.level
      }));

      // Update expiration time
      setBoxMonitoringExpires(prev => ({
        ...prev,
        [boxIndex]: message.expires_at || null
      }));

      // Update enabled metrics
      setBoxEnabledMetrics(prev => ({
        ...prev,
        [boxIndex]: message.enabled_metrics || []
      }));

      // Update agent stats (increment decisions)
      setBoxAgentStats(prev => {
        const current = prev[boxIndex] || { decisionsToday: 0, escalationsToday: 0 };
        return {
          ...prev,
          [boxIndex]: {
            decisionsToday: current.decisionsToday + 1,
            escalationsToday: message.level !== 'BASELINE' ? current.escalationsToday + 1 : current.escalationsToday
          }
        };
      });

      // Update last decision
      setBoxLastDecision(prev => ({
        ...prev,
        [boxIndex]: {
          timestamp: new Date(),
          action: `Changed to ${message.level}`,
          reason: message.reason || 'Monitoring level changed',
          confidence: 0.85 // Default confidence
        }
      }));

      // Add monitoring action event to patient log
      addPatientEvent(boxIndex, {
        timestamp: new Date().toISOString(),
        type: 'agent_action',  // Preserve specific type for green highlighting
        severity: message.level === 'CRITICAL' ? 'critical' : message.level === 'ENHANCED' ? 'warning' : 'normal',
        message: `⚡ ACTION: ${message.level} MONITORING ACTIVATED`,
        details: message.reason
      });

      // Add metric changes
      if (message.enabled_metrics && message.enabled_metrics.length > 0) {
        const metricsAdded = message.enabled_metrics.filter((m: string) =>
          !['heart_rate', 'respiratory_rate', 'crs_score'].includes(m)
        );

        if (metricsAdded.length > 0) {
          metricsAdded.forEach((metric: string) => {
            addPatientEvent(boxIndex, {
              timestamp: new Date().toISOString(),
              type: 'monitoring',
              severity: 'normal',
              message: `📊 Enabled: ${metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`,
              details: undefined
            });
          });
        }
      }

      // Add to global feed
      const patient = boxAssignments[boxIndex];
      if (patient) {
        addGlobalEvent({
          timestamp: new Date().toISOString(),
          patientId: boxIndex,
          patientName: patient.name,
          type: 'agent',
          severity: message.level === 'CRITICAL' ? 'high' : message.level === 'ENHANCED' ? 'moderate' : 'info',
          message: `🤖 Monitoring: ${message.level}`,
          details: message.reason
        });
      }
    }

    if (message.type === 'agent_thinking') {
      // Set analyzing state
      setBoxAgentAnalyzing(prev => ({
        ...prev,
        [boxIndex]: true
      }));

      // Add to activity log with specific type
      addPatientEvent(boxIndex, {
        timestamp: new Date().toISOString(),
        type: 'agent_thinking',  // Preserve specific type
        severity: 'info',
        message: 'Analyzing metrics...',
        details: message.message || 'AI agent evaluating patient condition'
      });

      // Clear after 3 seconds
      setTimeout(() => {
        setBoxAgentAnalyzing(prev => ({
          ...prev,
          [boxIndex]: false
        }));
      }, 3000);
    }

    if (message.type === 'agent_reasoning') {
      // Add reasoning to activity log with rich metadata
      addPatientEvent(boxIndex, {
        timestamp: new Date().toISOString(),
        type: 'agent_reasoning',  // Preserve specific type
        severity: 'info',
        message: `🧠 REASONING: "${message.reasoning}"`,
        details: message.concerns && message.concerns.length > 0 ? `Concerns: [${message.concerns.join(', ')}]` : undefined,
        confidence: message.confidence,
        concerns: message.concerns || []
      });
    }

    if (message.type === 'agent_alert') {
      // Update last decision with full details
      setBoxLastDecision(prev => ({
        ...prev,
        [boxIndex]: {
          timestamp: new Date(),
          action: message.message || 'Alert triggered',
          reason: message.reasoning || message.reason || 'Alert condition detected',
          confidence: message.confidence || 0.8
        }
      }));

      // Add event to patient log
      addPatientEvent(boxIndex, {
        timestamp: new Date().toISOString(),
        type: 'agent',
        severity: message.severity?.toLowerCase() || 'info',
        message: message.message,
        details: message.reasoning
      });

      // Add to global feed
      const patient = boxAssignments[boxIndex];
      if (patient) {
        addGlobalEvent({
          timestamp: new Date().toISOString(),
          patientId: boxIndex,
          patientName: patient.name,
          type: 'agent',
          severity: message.severity?.toLowerCase() || 'info',
          message: message.message,
          details: message.reasoning
        });
      }
    }
  }, [addPatientEvent, addGlobalEvent, boxAssignments]);

  // Navigation between modes
  const onPatientClicked = (boxIndex: number) => {
    setSelectedPatientId(boxIndex);
    setViewMode('detail');
  };

  const onBackToOverview = () => {
    setViewMode('overview');
    // Keep selected patient ID so CV data still updates
  };

  // Handle alert resolution
  const handleAlertResolve = async (alertId: string) => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/alerts/${alertId}?status=resolved`, {
        method: 'PATCH',
      });

      if (response.ok) {
        // Remove alert from local state immediately for responsive UI
        setAlerts(prev => prev.filter(alert => alert.id !== alertId));
        console.log('✅ Alert resolved:', alertId);
      } else {
        console.error('❌ Failed to resolve alert');
      }
    } catch (err) {
      console.error('❌ Error resolving alert:', err);
    }
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
    const apiUrl = getApiUrl();
    
    // Fetch patients from backend
    fetch(`${apiUrl}/patients`)
      .then(res => res.json())
      .then(data => {
        setPatients(data);
        // Select first patient by default
        if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        }
      })
      .catch(err => console.error('Error fetching patients:', err));

    // Fetch initial alerts
    const fetchAlerts = () => {
      fetch(`${apiUrl}/alerts?status=active&limit=10`)
        .then(res => res.json())
        .then(data => {
          // Handle both array response and object with alerts property
          const alertsArray = Array.isArray(data) ? data : (data.alerts || []);
          setAlerts(alertsArray);
          setIsLoadingAlerts(false);
        })
        .catch(err => {
          console.error('Error fetching alerts:', err);
          setIsLoadingAlerts(false);
        });
    };

    fetchAlerts();

    // Poll for alerts every 5 seconds
    const alertInterval = setInterval(fetchAlerts, 5000);

    // Fetch stats
    fetch(`${apiUrl}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Error fetching stats:', err));

    return () => clearInterval(alertInterval);
  }, []);

  // Update stats when alerts change
  useEffect(() => {
    const activeCount = alerts.filter(a => a.status === 'active').length;
    setStats(prev => ({ ...prev, active_alerts: activeCount }));
  }, [alerts]);

  // No longer need displayedPatients - we use boxAssignments instead

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-2 border-neutral-950 bg-surface">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo */}
            <div>
              <h1 className="text-lg font-light text-neutral-950 uppercase tracking-wider">
                Haven
              </h1>
            </div>

            {/* Center: Navigation */}
            <nav className="flex items-center gap-1">
              <a
                href="/dashboard"
                className="px-6 py-2 label-uppercase text-xs text-neutral-950 border-b-2 border-primary-700 hover:bg-neutral-50 transition-colors"
              >
                Dashboard
              </a>
              <a
                href="/dashboard/floorplan"
                className="px-6 py-2 label-uppercase text-xs text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50 transition-colors"
              >
                Floor Plan
              </a>
              <a
                href="/stream"
                className="px-6 py-2 label-uppercase text-xs text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50 transition-colors"
              >
                Stream
              </a>
            </nav>

            {/* Right side: Alerts & User */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setManualAlertsOpen(true)}
                className="px-4 py-2 text-xs font-medium uppercase tracking-wide border border-neutral-300 rounded-full text-neutral-700 hover:text-neutral-950 hover:border-neutral-950 transition-colors"
              >
                Manual Alerts
              </button>
              {/* Notifications */}
              <button className="relative p-2 text-neutral-500 hover:text-neutral-950 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
              </button>

              {/* User avatar */}
              <div className="w-9 h-9 rounded-full bg-neutral-200 border border-neutral-300 flex items-center justify-center text-neutral-600 text-sm font-medium">
                U
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        {/* Stats Bar */}
        {/* <div className="mb-6">
          <StatsBar stats={stats} alertCount={alerts.length} />
        </div> */}

        {viewMode === 'overview' ? (
          // OVERVIEW MODE: Stacked management and monitoring + activity feed
          <div className="grid grid-cols-12 gap-6">
            {/* Left Panel - Patient Management & Monitoring (8 columns) */}
            <div className="col-span-8 space-y-6">
              {/* Patient Management */}
              <div className="h-[400px]">
                <PatientManagement />
              </div>

              {/* Patient Monitoring */}
              <div>
                <div className="mb-4">
                  <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950 border-b-2 border-neutral-950 pb-2 inline-block">Patient Monitoring</h2>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {boxAssignments.map((patient, boxIndex) => {
                // Empty box - show + button (only show if it's the last empty box)
                if (!patient) {
                  // Check if this is the last empty box (should be the only one)
                  const isLastEmptyBox = boxIndex === boxAssignments.length - 1;
                  if (!isLastEmptyBox) return null; // Skip rendering if not the last empty box
                  
                  return (
                    <div key={boxIndex} className="flex flex-col">
                      <div className="relative overflow-hidden border border-neutral-200 bg-neutral-50 rounded-lg">
                        <div className="w-full aspect-video flex items-center justify-center">
                          <button
                            onClick={() => openPatientSelectionForBox(boxIndex)}
                            className="w-16 h-16 bg-surface hover:bg-primary-700 border border-neutral-300 hover:border-primary-700 text-neutral-400 hover:text-white text-3xl transition-all hover:scale-105 font-light rounded-lg"
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="bg-surface border border-neutral-200 border-t-0 px-4 py-3 rounded-b-lg">
                        <p className="label-uppercase text-neutral-400 text-center">Empty</p>
                      </div>
                    </div>
                  );
                }

                // Assigned box - show VideoPlayer with patient stream
                return (
                  <div key={boxIndex} className="flex flex-col">
                    <div 
                      className="cursor-pointer"
                      onClick={() => onPatientClicked(boxIndex)}
                    >
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
                        onAgentMessage={(pid, msg) => handleAgentMessage(boxIndex, msg)}
                        monitoringConditions={boxMonitoringConditions[boxIndex] || []}
                      />
                    </div>
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
            </div>

            {/* Right Column - Activity Feed (4 columns) */}
            <div className="col-span-4 h-[calc(100vh-180px)] min-h-[420px]">
              <GlobalActivityFeed
                events={globalEventFeed}
                alerts={alerts}
                isLoading={isLoadingAlerts}
                onPatientClick={onPatientClicked}
                onAlertResolve={handleAlertResolve}
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
                      onAgentMessage={(pid, msg) => handleAgentMessage(selectedPatientId, msg)}
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
                  monitoringLevel={selectedPatientId !== null ? (boxMonitoringLevels[selectedPatientId] || 'BASELINE') : 'BASELINE'}
                  monitoringExpiresAt={selectedPatientId !== null ? (boxMonitoringExpires[selectedPatientId] || null) : null}
                  enabledMetrics={selectedPatientId !== null ? (boxEnabledMetrics[selectedPatientId] || ['heart_rate', 'respiratory_rate', 'crs_score']) : []}
                  isAgentAnalyzing={selectedPatientId !== null ? (boxAgentAnalyzing[selectedPatientId] || false) : false}
                  lastAgentDecision={selectedPatientId !== null ? (boxLastDecision[selectedPatientId] || null) : null}
                  agentStats={selectedPatientId !== null ? (boxAgentStats[selectedPatientId] || { decisionsToday: 0, escalationsToday: 0 }) : { decisionsToday: 0, escalationsToday: 0 }}
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

      <ManualAlertsPanel
        isOpen={isManualAlertsOpen}
        onClose={() => setManualAlertsOpen(false)}
      />
    </div>
  );
}
