'use client';

import { useEffect, useState, useCallback } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import InfoBar from '@/components/InfoBar';
import DetailPanel from '@/components/DetailPanel';
import StatsBar from '@/components/StatsBar';

interface Patient {
  id: number;
  name: string;
  age: number;
  condition: string;
  baseline_vitals: {
    heart_rate: number;
  };
}

interface CVData {
  crs_score: number;
  heart_rate: number;
  respiratory_rate: number;
  alert?: boolean;
}

interface Alert {
  patient_id: number;
  message: string;
  crs_score: number;
  heart_rate: number;
  timestamp: string;
}

export default function DashboardPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [cvDataMap, setCvDataMap] = useState<Map<number, CVData | null>>(new Map());
  const [stats, setStats] = useState({
    patients_monitored: 47,
    active_alerts: 0,
    daily_cost_savings: 17550
  });

  // Callback to update CV data for a specific patient
  const handleCvDataUpdate = useCallback((patientId: number, data: CVData | null) => {
    setCvDataMap(prev => {
      const newMap = new Map(prev);
      newMap.set(patientId, data);
      return newMap;
    });
  }, []);

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

  // Display first 5 pre-recorded + 1 live feed
  const displayedPatients = [
    ...patients.slice(0, 5),
    {
      id: 999,  // Special ID for live feed
      name: "LIVE DEMO",
      age: 0,
      condition: "Live Webcam Stream",
      baseline_vitals: { heart_rate: 75 }
    }
  ];

  // Get selected patient and its CV data
  const selectedPatient = displayedPatients.find(p => p.id === selectedPatientId) || null;
  const selectedCvData = selectedPatientId ? cvDataMap.get(selectedPatientId) || null : null;

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

            {displayedPatients.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {displayedPatients.map((patient, index) => {
                  const isLive = index === 5;
                  const patientCvData = cvDataMap.get(patient.id);

                  return (
                    <div key={patient.id} className="flex flex-col">
                      <VideoPlayer
                        patient={patient}
                        isLive={isLive}
                        isSelected={selectedPatientId === patient.id}
                        onCvDataUpdate={(data) => handleCvDataUpdate(patient.id, data)}
                      />
                      <InfoBar
                        patientId={isLive ? 'LIVE' : patient.id}
                        patientName={patient.name}
                        heartRate={patientCvData?.heart_rate}
                        crsScore={patientCvData?.crs_score}
                        isLive={isLive}
                        isSelected={selectedPatientId === patient.id}
                        onClick={() => setSelectedPatientId(patient.id)}
                      />
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-12 text-center">
                <p className="text-slate-400">Loading patients...</p>
              </div>
            )}
          </div>

          {/* Detail Panel (Right - 4 columns) */}
          <div className="col-span-4">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">Patient Details</h2>
              <p className="text-sm text-slate-400">Detailed vitals and AI analysis</p>
            </div>
            <DetailPanel
              patient={selectedPatient}
              cvData={selectedCvData}
              isLive={selectedPatient?.id === 999}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

