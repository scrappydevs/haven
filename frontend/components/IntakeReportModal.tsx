'use client';

import { useState, useEffect } from 'react';

interface IntakeReport {
  id: string;
  patient_id: string;
  session_id: string;
  chief_complaint: string;
  symptoms: string[];
  duration: string;
  severity: number;
  medications: string;
  allergies: string;
  prior_episodes: string;
  vitals: {
    heart_rate?: number;
    respiratory_rate?: number;
    stress_indicator?: number;
    samples_collected?: number;
  };
  urgency_level: 'low' | 'medium' | 'high';
  ai_summary: string;
  transcript: Array<{ role: string; content: string; timestamp: string }>;
  status: string;
  created_at: string;
  interview_duration_seconds: number;
}

interface Props {
  intakeId: string;
  onClose: () => void;
  onReviewed: () => void;
}

export default function IntakeReportModal({ intakeId, onClose, onReviewed }: Props) {
  const [report, setReport] = useState<IntakeReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRoom, setSelectedRoom] = useState('');
  const [assigning, setAssigning] = useState(false);

  useEffect(() => {
    fetchReport();
  }, [intakeId]);

  const fetchReport = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/intake/${intakeId}`);

      if (!response.ok) throw new Error('Failed to fetch report');

      const data = await response.json();
      setReport(data);
      setError('');
    } catch (err) {
      console.error('Error fetching report:', err);
      setError('Failed to load intake report');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkReviewed = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/api/intake/${intakeId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewer_id: 'current_user' }) // TODO: Get actual user ID
      });

      onReviewed();
    } catch (err) {
      console.error('Error marking as reviewed:', err);
      alert('Failed to mark as reviewed');
    }
  };

  const handleAssignRoom = async () => {
    if (!selectedRoom) {
      alert('Please select a room');
      return;
    }

    setAssigning(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/api/intake/${intakeId}/assign-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: selectedRoom })
      });

      alert('Patient assigned to room successfully');
      onReviewed();
    } catch (err) {
      console.error('Error assigning room:', err);
      alert('Failed to assign room');
    } finally {
      setAssigning(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full">
          <div className="flex items-center justify-center">
            <svg className="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={onClose} className="px-4 py-2 bg-gray-600 text-white rounded">Close</button>
        </div>
      </div>
    );
  }

  const urgencyColors = {
    high: 'bg-red-100 text-red-800 border-red-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-green-100 text-green-800 border-green-300'
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
          <div>
            <h2 className="text-2xl font-bold">Intake Report</h2>
            <p className="text-blue-100 text-sm mt-1">Patient: {report.patient_id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[calc(100vh-16rem)] overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Summary */}
            <div className="lg:col-span-2 space-y-6">
              {/* AI Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  AI Summary
                </h3>
                <p className="text-gray-700">{report.ai_summary}</p>
              </div>

              {/* Chief Complaint */}
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Chief Complaint</h3>
                <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{report.chief_complaint || 'Not specified'}</p>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2 text-sm">Duration</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{report.duration || 'Not specified'}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2 text-sm">Severity</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {report.severity ? `${report.severity}/10` : 'Not rated'}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2 text-sm">Medications</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{report.medications || 'None reported'}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2 text-sm">Allergies</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{report.allergies || 'None reported'}</p>
                </div>
              </div>

              {/* Prior Episodes */}
              {report.prior_episodes && (
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Prior Episodes</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{report.prior_episodes}</p>
                </div>
              )}

              {/* Transcript */}
              <div>
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  Full Transcript ({report.transcript?.length || 0} exchanges)
                </h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto space-y-3">
                  {report.transcript?.map((item, idx) => (
                    <div key={idx} className={`p-3 rounded ${item.role === 'assistant' ? 'bg-blue-100' : 'bg-white border border-gray-200'}`}>
                      <div className="flex items-start">
                        <span className="font-semibold text-sm mr-2 text-gray-700">
                          {item.role === 'assistant' ? '🤖 AI:' : '👤 Patient:'}
                        </span>
                        <p className="text-sm text-gray-700 flex-1">{item.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column - Metadata & Actions */}
            <div className="space-y-6">
              {/* Urgency Badge */}
              <div className={`border-2 rounded-lg p-4 ${urgencyColors[report.urgency_level]}`}>
                <h3 className="font-bold text-lg mb-1">Urgency Level</h3>
                <p className="text-2xl font-bold uppercase">{report.urgency_level}</p>
              </div>

              {/* Vitals */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                  </svg>
                  Vitals
                </h3>
                <div className="space-y-2 text-sm">
                  {report.vitals?.heart_rate && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Heart Rate:</span>
                      <span className="font-semibold">{report.vitals.heart_rate} bpm</span>
                    </div>
                  )}
                  {report.vitals?.respiratory_rate && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Respiratory Rate:</span>
                      <span className="font-semibold">{report.vitals.respiratory_rate} /min</span>
                    </div>
                  )}
                  {!report.vitals?.heart_rate && !report.vitals?.respiratory_rate && (
                    <p className="text-gray-500 italic">No vitals collected</p>
                  )}
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3">Interview Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duration:</span>
                    <span className="font-semibold">{Math.floor(report.interview_duration_seconds / 60)}m {report.interview_duration_seconds % 60}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed:</span>
                    <span className="font-semibold">{new Date(report.created_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Session ID:</span>
                    <span className="font-mono text-xs">{report.session_id}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <button
                  onClick={handleMarkReviewed}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition"
                >
                  ✓ Mark as Reviewed
                </button>

                <div className="border border-gray-300 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Assign to Room
                  </label>
                  <select
                    value={selectedRoom}
                    onChange={(e) => setSelectedRoom(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 mb-3"
                  >
                    <option value="">Select room...</option>
                    <option value="101">Room 101</option>
                    <option value="102">Room 102</option>
                    <option value="103">Room 103</option>
                    <option value="104">Room 104</option>
                    <option value="105">Room 105</option>
                  </select>
                  <button
                    onClick={handleAssignRoom}
                    disabled={!selectedRoom || assigning}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded transition disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {assigning ? 'Assigning...' : '→ Assign to Room'}
                  </button>
                </div>

                <button
                  onClick={onClose}
                  className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-4 rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
