'use client';

import { useState, useEffect } from 'react';
import IntakeReportModal from './IntakeReportModal';

interface IntakeReport {
  id: string;
  patient_id: string;
  chief_complaint: string;
  urgency_level: 'low' | 'medium' | 'high';
  vitals: {
    heart_rate?: number;
    respiratory_rate?: number;
  };
  created_at: string;
  interview_duration_seconds: number;
  status: string;
}

export default function IntakeQueue() {
  const [intakes, setIntakes] = useState<IntakeReport[]>([]);
  const [selectedIntake, setSelectedIntake] = useState<IntakeReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchIntakes = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/intake/pending`);

      if (!response.ok) throw new Error('Failed to fetch intakes');

      const data = await response.json();
      setIntakes(data);
      setError('');
    } catch (err) {
      console.error('Error fetching intakes:', err);
      setError('Failed to load intake queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntakes();

    // Poll for updates every 10 seconds
    const interval = setInterval(fetchIntakes, 10000);

    // Listen for WebSocket notifications of new intakes
    const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000').replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/view`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_intake') {
          fetchIntakes(); // Refresh queue
        }
      } catch (e) {
        console.error('WebSocket message error:', e);
      }
    };

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  const handleIntakeReviewed = () => {
    fetchIntakes();
    setSelectedIntake(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center">
          <svg className="animate-spin h-10 w-10 text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading intake queue...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-red-700 font-medium">{error}</p>
        <button
          onClick={fetchIntakes}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Intake Queue</h2>
          <p className="text-gray-600 text-sm mt-1">
            {intakes.length} {intakes.length === 1 ? 'patient' : 'patients'} awaiting review
          </p>
        </div>
        <button
          onClick={fetchIntakes}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Queue List */}
      {intakes.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 text-lg font-medium">No pending intakes</p>
          <p className="text-gray-400 text-sm mt-2">New intakes will appear here automatically</p>
        </div>
      ) : (
        <div className="space-y-3">
          {intakes.map((intake) => (
            <IntakeCard
              key={intake.id}
              intake={intake}
              onClick={() => setSelectedIntake(intake)}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      {selectedIntake && (
        <IntakeReportModal
          intakeId={selectedIntake.id}
          onClose={() => setSelectedIntake(null)}
          onReviewed={handleIntakeReviewed}
        />
      )}
    </div>
  );
}

function IntakeCard({ intake, onClick }: { intake: IntakeReport; onClick: () => void }) {
  const urgencyConfig = {
    high: {
      bg: 'bg-red-50',
      border: 'border-red-300',
      badge: 'bg-red-600',
      text: 'text-red-700',
      badgeText: 'HIGH PRIORITY'
    },
    medium: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-300',
      badge: 'bg-yellow-600',
      text: 'text-yellow-700',
      badgeText: 'MEDIUM PRIORITY'
    },
    low: {
      bg: 'bg-green-50',
      border: 'border-green-300',
      badge: 'bg-green-600',
      text: 'text-green-700',
      badgeText: 'STANDARD'
    }
  };

  const config = urgencyConfig[intake.urgency_level];

  const timeAgo = (dateString: string) => {
    const seconds = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <button
      onClick={onClick}
      className={`w-full ${config.bg} border-2 ${config.border} rounded-lg p-4 hover:shadow-lg transition duration-200 text-left`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Priority Badge */}
          <div className="flex items-center space-x-3 mb-2">
            <span className={`${config.badge} text-white text-xs font-bold px-3 py-1 rounded-full`}>
              {config.badgeText}
            </span>
            <span className="text-sm text-gray-500">{timeAgo(intake.created_at)}</span>
          </div>

          {/* Patient Info */}
          <div className="flex items-center space-x-4 mb-2">
            <h3 className={`text-lg font-bold ${config.text}`}>
              {intake.patient_id}
            </h3>
            <span className="text-gray-400">•</span>
            <span className="text-gray-700 font-medium">
              {intake.chief_complaint || 'Not specified'}
            </span>
          </div>

          {/* Vitals Preview */}
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            {intake.vitals?.heart_rate && (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-1 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                </svg>
                HR: {intake.vitals.heart_rate} bpm
              </div>
            )}
            {intake.vitals?.respiratory_rate && (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-1 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
                </svg>
                RR: {intake.vitals.respiratory_rate} /min
              </div>
            )}
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {Math.floor(intake.interview_duration_seconds / 60)}m {intake.interview_duration_seconds % 60}s interview
            </div>
          </div>
        </div>

        {/* Action Arrow */}
        <div className="ml-4">
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </button>
  );
}
