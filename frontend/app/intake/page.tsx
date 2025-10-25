'use client';

import { useState, useEffect } from 'react';
import { LiveKitRoom, RoomAudioRenderer, useDataChannel, useVoiceAssistant } from '@livekit/components-react';
import '@livekit/components-styles';

export default function PatientIntakePage() {
  const [patientId, setPatientId] = useState('');
  const [token, setToken] = useState('');
  const [livekitUrl, setLivekitUrl] = useState('');
  const [stage, setStage] = useState<'select' | 'interview' | 'complete'>('select');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const startIntake = async () => {
    if (!patientId.trim()) {
      setError('Please enter your Patient ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/intake/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId.trim() })
      });

      if (!response.ok) {
        throw new Error('Failed to start intake session');
      }

      const data = await response.json();
      setToken(data.token);
      setLivekitUrl(data.url);
      setStage('interview');
    } catch (err) {
      console.error('Intake start error:', err);
      setError('Failed to start intake. Please try again or contact staff.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      startIntake();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-800">Haven Health</h1>
          <p className="text-sm text-gray-500">AI-Powered Patient Intake</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        {stage === 'select' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
              {/* Icon */}
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>

              <h2 className="text-3xl font-bold text-gray-800 text-center mb-2">
                Welcome to Check-In
              </h2>
              <p className="text-gray-600 text-center mb-8">
                Our AI assistant will help gather information before your appointment
              </p>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label htmlFor="patientId" className="block text-sm font-medium text-gray-700 mb-2">
                    Patient ID
                  </label>
                  <input
                    id="patientId"
                    type="text"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="e.g., P-001"
                    disabled={loading}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    autoFocus
                  />
                </div>

                <button
                  onClick={startIntake}
                  disabled={loading || !patientId.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Starting...
                    </>
                  ) : (
                    'Start Check-In'
                  )}
                </button>
              </div>

              {/* Instructions */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Before you begin:</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Have your medication list ready
                  </li>
                  <li className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Know your known allergies
                  </li>
                  <li className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Be in a quiet space if possible
                  </li>
                  <li className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Allow microphone access when prompted
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {stage === 'interview' && token && livekitUrl && (
          <LiveKitRoom
            token={token}
            serverUrl={livekitUrl}
            connect={true}
            audio={true}
            video={false}  // Audio-only for intake
            onDisconnected={() => setStage('complete')}
          >
            <IntakeInterviewView patientId={patientId} />
            <RoomAudioRenderer />
          </LiveKitRoom>
        )}

        {stage === 'complete' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8 text-center border border-gray-100">
              {/* Success Icon */}
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <h2 className="text-3xl font-bold text-gray-800 mb-3">
                Thank You!
              </h2>
              <p className="text-gray-600 mb-6 text-lg">
                Your intake is complete.
              </p>
              <p className="text-gray-500 mb-8">
                A healthcare provider will review your information and see you shortly.
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  You may close this window or wait in the virtual waiting room.
                </p>
              </div>

              <button
                onClick={() => {
                  setStage('select');
                  setPatientId('');
                  setToken('');
                  setLivekitUrl('');
                }}
                className="mt-6 text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Start Another Check-In
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function IntakeInterviewView({ patientId }: { patientId: string }) {
  const [agentState, setAgentState] = useState<'connecting' | 'listening' | 'speaking' | 'thinking'>('connecting');
  const [transcriptItems, setTranscriptItems] = useState<Array<{ role: string; text: string; timestamp: Date }>>([]);
  const { state: assistantState } = useVoiceAssistant();

  useEffect(() => {
    // Map LiveKit agent state to our UI state
    if (assistantState === 'connecting') {
      setAgentState('connecting');
    } else if (assistantState === 'listening') {
      setAgentState('listening');
    } else if (assistantState === 'speaking') {
      setAgentState('speaking');
    } else if (assistantState === 'thinking') {
      setAgentState('thinking');
    }
  }, [assistantState]);

  const stateConfig = {
    connecting: {
      color: 'bg-gray-500',
      pulse: false,
      icon: '🔌',
      text: 'Connecting to Haven AI...',
      subtext: 'Please wait'
    },
    listening: {
      color: 'bg-green-500',
      pulse: true,
      icon: '🎤',
      text: 'Listening...',
      subtext: 'Speak naturally'
    },
    speaking: {
      color: 'bg-blue-500',
      pulse: true,
      icon: '🗣️',
      text: 'Haven AI is speaking...',
      subtext: 'Please listen'
    },
    thinking: {
      color: 'bg-yellow-500',
      pulse: true,
      icon: '🤔',
      text: 'Processing...',
      subtext: 'Just a moment'
    }
  };

  const currentState = stateConfig[agentState];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Patient Intake</h2>
              <p className="text-blue-100 text-sm mt-1">Patient ID: {patientId}</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${currentState.pulse ? 'animate-pulse' : ''} ${currentState.color}`} />
              <span className="text-sm font-medium">Live</span>
            </div>
          </div>
        </div>

        {/* Main Interview Area */}
        <div className="p-8">
          {/* Agent Avatar & Status */}
          <div className="flex flex-col items-center justify-center py-12">
            <div className={`w-32 h-32 rounded-full flex items-center justify-center mb-6 transition-all duration-300 ${currentState.color} ${currentState.pulse ? 'animate-pulse' : ''}`}>
              <span className="text-6xl">{currentState.icon}</span>
            </div>

            <h3 className="text-2xl font-semibold text-gray-800 mb-2">
              {currentState.text}
            </h3>
            <p className="text-gray-500 text-lg">
              {currentState.subtext}
            </p>

            {/* Audio Level Indicator (when listening) */}
            {agentState === 'listening' && (
              <div className="mt-6 flex items-center space-x-2">
                <div className="w-1 h-8 bg-green-400 rounded animate-pulse" style={{ animationDelay: '0ms' }} />
                <div className="w-1 h-12 bg-green-400 rounded animate-pulse" style={{ animationDelay: '100ms' }} />
                <div className="w-1 h-10 bg-green-400 rounded animate-pulse" style={{ animationDelay: '200ms' }} />
                <div className="w-1 h-14 bg-green-400 rounded animate-pulse" style={{ animationDelay: '300ms' }} />
                <div className="w-1 h-8 bg-green-400 rounded animate-pulse" style={{ animationDelay: '400ms' }} />
              </div>
            )}
          </div>

          {/* Instructions */}
          <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Interview Tips
            </h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Speak clearly and naturally
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The AI will ask you about your chief complaint, symptoms, medications, and allergies
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                If you mention urgent symptoms (chest pain, difficulty breathing, etc.), the interview will be expedited
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The interview typically takes 3-5 minutes
              </li>
            </ul>
          </div>

          {/* Transcript (Optional - can be hidden) */}
          {transcriptItems.length > 0 && (
            <div className="mt-8">
              <h4 className="font-semibold text-gray-700 mb-4">Conversation</h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {transcriptItems.map((item, idx) => (
                  <div key={idx} className={`p-3 rounded-lg ${item.role === 'agent' ? 'bg-blue-50 border border-blue-100' : 'bg-gray-50 border border-gray-100'}`}>
                    <div className="flex items-start">
                      <span className="font-semibold text-sm text-gray-700 mr-2">
                        {item.role === 'agent' ? 'Haven AI:' : 'You:'}
                      </span>
                      <span className="text-sm text-gray-600 flex-1">{item.text}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
