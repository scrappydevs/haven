'use client';

import { useEffect, useRef, useState } from 'react';
import PatientSearchModal from '@/components/PatientSearchModal';
import AnalysisModeSelector, { AnalysisMode } from '@/components/AnalysisModeSelector';
import { getApiUrl, getWsUrl } from '@/lib/api';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

export default function PatientViewPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const captureCleanupRef = useRef<(() => void) | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const isConnectingRef = useRef<boolean>(false);

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [tempPatient, setTempPatient] = useState<Patient | null>(null);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('enhanced');
  const [showPatientModal, setShowPatientModal] = useState(true); // Start with modal open
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [activeStreams, setActiveStreams] = useState<string[]>([]);
  const [viewStarted, setViewStarted] = useState(false); // Track if view has been started

  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [fps, setFps] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isMicActive, setIsMicActive] = useState(false);

  useEffect(() => {
    return () => {
      if (wsRef.current || streamRef.current) {
        console.log('🧹 Component unmounting - cleaning up stream');
        if (captureCleanupRef.current) {
          captureCleanupRef.current();
        }
        if (wsRef.current) {
          wsRef.current.close();
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
      }
    };
  }, []);

  const openPatientSelection = async () => {
    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/streams/active`);
      const data = await res.json();
      setActiveStreams(data.active_streams || []);
      setShowPatientModal(true);
    } catch (error) {
      console.error('Error fetching active streams:', error);
      setShowPatientModal(true);
    }
  };

  const startStreaming = async () => {
    if (!selectedPatient) {
      setError('Please select a patient first');
      return;
    }

    if (isStreaming || isConnecting || isConnectingRef.current) {
      console.log('⚠️ Already streaming or connecting (prevented duplicate)');
      return;
    }

    isConnectingRef.current = true;

    try {
      setIsConnecting(true);
      setError(null);

      if (captureCleanupRef.current) {
        captureCleanupRef.current();
        captureCleanupRef.current = null;
      }

      if (wsRef.current) {
        console.log('⚠️  Closing existing WebSocket before starting new one');
        try {
          wsRef.current.close();
        } catch (e) {
          console.log('   (Error closing old WS, continuing anyway)');
        }
        wsRef.current = null;
      }

      console.log('📹 Requesting webcam access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        }
      });
      streamRef.current = stream;
      console.log('✅ Webcam access granted');

      const video = videoRef.current;
      if (!video) {
        throw new Error('Video element not found');
      }

      video.srcObject = stream;

      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Video load timeout')), 5000);

        video.onloadedmetadata = () => {
          clearTimeout(timeout);
          console.log('✅ Video metadata loaded');
          resolve();
        };
      });

      try {
        await video.play();
        console.log('✅ Video playing');
      } catch (playError) {
        console.error('Video play error:', playError);
        throw new Error('Failed to play video');
      }

      const wsUrl = getWsUrl(`/ws/stream/${selectedPatient.patient_id}`);
      console.log(`🔌 Connecting to WebSocket for patient ${selectedPatient.patient_id}:`, wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.warn(`⏱️  Connection timeout - current state: ${ws.readyState}`);
          ws.close();
          setError('Connection timeout. Is the backend running on port 8000?');
          setIsConnecting(false);
          isConnectingRef.current = false;
        }
      }, 5000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log('✅ WebSocket ONOPEN fired - connection established!');

        const handshake = {
          type: 'handshake',
          analysis_mode: analysisMode
        };
        console.log(`📋 Sending handshake:`, JSON.stringify(handshake));
        ws.send(JSON.stringify(handshake));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'error') {
          console.error('❌ Server error:', data.message);
          setError(data.message);
          setIsConnecting(false);
          ws.close();
          return;
        }

        if (data.type === 'connected') {
          console.log('✅ Handshake confirmed, starting stream');
          setIsStreaming(true);
          setIsConnecting(false);
          isConnectingRef.current = false;

          if (data.warning) {
            console.warn('⚠️ WebSocket warning:', data.warning);
          }

          const cleanup = startCapture();
          captureCleanupRef.current = cleanup;
        }
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        
        const hadConnection = isStreaming;
        const wasAttemptingConnection = isConnecting || isConnectingRef.current;
        
        console.log('❌ Disconnected from server. Code:', event.code, 'Reason:', event.reason);
        
        setIsStreaming(false);
        setIsConnecting(false);
        isConnectingRef.current = false;

        if (!hadConnection && !wasAttemptingConnection && event.code === 1006) {
          console.warn('⚠️  Ignoring transient connection close (likely React dev mode duplicate)');
          return;
        }

        if (event.reason) {
          setError(event.reason);
        } else if (event.code === 4090) {
          setError('This patient already has an active stream. Please stop the other stream before starting a new one.');
        } else if (event.code === 1006 && wasAttemptingConnection) {
          setError('Connection failed. Make sure backend is running: cd backend && python3 main.py');
        }
      };

      ws.onerror = (event) => {
        console.warn('⚠️  WebSocket error (may be transient):', event);
      };

    } catch (err: any) {
      console.error('Error starting stream:', err);
      setError(err.message || 'Could not access webcam. Please allow camera permissions.');
      setIsConnecting(false);
      isConnectingRef.current = false;

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  };

  const startCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) {
      console.log('⚠️ Video or canvas not found for capture');
      return () => {};
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.log('⚠️ Canvas context not available');
      return () => {};
    }

    let frameCount = 0;
    let lastFpsUpdate = Date.now();
    let isActive = true;
    let timeoutId: NodeJS.Timeout | null = null;

    const captureFrame = () => {
      if (!isActive || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.log('⏹️ Stopping capture. Active:', isActive, 'WS state:', wsRef.current?.readyState);
        return;
      }

      try {
        const targetWidth = 640;
        const targetHeight = 360;

        if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
          canvas.width = targetWidth;
          canvas.height = targetHeight;
        }

        ctx.drawImage(video, 0, 0, targetWidth, targetHeight);
        const frameData = canvas.toDataURL('image/jpeg', 0.7);

        wsRef.current.send(JSON.stringify({
          type: 'frame',
          frame: frameData
        }));

        frameCount++;
        const now = Date.now();
        if (now - lastFpsUpdate >= 1000) {
          setFps(frameCount);
          frameCount = 0;
          lastFpsUpdate = now;
        }

        timeoutId = setTimeout(captureFrame, 33);
      } catch (error) {
        console.error('❌ Error in capture frame:', error);
        isActive = false;
      }
    };

    console.log('▶️ Starting frame capture');
    captureFrame();

    return () => {
      console.log('🛑 Cleanup capture function called');
      isActive = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  };

  const stopStreaming = () => {
    console.log('🛑 Stopping stream...');

    if (captureCleanupRef.current) {
      captureCleanupRef.current();
      captureCleanupRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('Stopped track:', track.kind);
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
    setIsConnecting(false);
    isConnectingRef.current = false;
    setFps(0);
    setViewStarted(false);
    console.log('✅ Stream stopped');
  };

  const handleStartView = () => {
    setViewStarted(true);
    startStreaming();
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Show initial patient selection modal */}
      {!selectedPatient && (
        <>
          {/* Patient Search Modal (Step 1) */}
          <PatientSearchModal
            isOpen={showPatientModal}
            onClose={() => setShowPatientModal(false)}
            onSelect={(patient) => {
              setTempPatient(patient);
              setShowPatientModal(false);
              setShowModeSelector(true);
            }}
            activeStreams={activeStreams}
          />

          {/* Analysis Mode Selector Modal (Step 2) */}
          {showModeSelector && tempPatient && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div
                className="absolute inset-0 bg-neutral-950/80"
                onClick={() => setShowModeSelector(false)}
              />
              <div className="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto rounded-lg">
                <AnalysisModeSelector
                  patient={tempPatient}
                  onConfirm={(mode) => {
                    setSelectedPatient(tempPatient);
                    setAnalysisMode(mode);
                    setShowModeSelector(false);

                    if (tempPatient) {
                      localStorage.setItem(
                        `analysis-mode-${tempPatient.patient_id}`,
                        mode
                      );
                      console.log(`💾 Saved analysis mode for ${tempPatient.patient_id}:`, mode);
                    }

                    setTempPatient(null);
                    console.log(`✅ Selected patient ${tempPatient.patient_id} with mode:`, mode);
                  }}
                  onBack={() => {
                    setShowModeSelector(false);
                    setShowPatientModal(true);
                  }}
                />
              </div>
            </div>
          )}
        </>
      )}

      {/* Once patient is selected, show the view */}
      {selectedPatient && !viewStarted && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-neutral-950/40">
          <div className="bg-white border border-neutral-200 max-w-2xl w-full p-8 rounded-lg">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-playfair font-black text-primary-950 mb-2">Patient View</h2>
              <p className="text-neutral-600">Ready to start monitoring</p>
            </div>

            {/* Patient Info Card */}
            <div className="bg-neutral-50 border border-neutral-200 p-6 mb-6 rounded-lg">
              <div className="flex items-center gap-6">
                <img
                  src={selectedPatient.photo_url}
                  alt={selectedPatient.name}
                  className="w-24 h-24 object-cover rounded-lg"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-2xl font-light text-neutral-950">{selectedPatient.name}</h3>
                    <span className="label-uppercase bg-primary-700 text-white px-3 py-1">
                      {selectedPatient.patient_id}
                    </span>
                  </div>
                <p className="body-default text-neutral-700 mb-1">
                  {selectedPatient.age}y/o • {selectedPatient.gender}
                </p>
                <p className="body-default text-neutral-950 font-medium">{selectedPatient.condition}</p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="label-uppercase text-neutral-700">Mode:</span>
                  <span className={`label-uppercase px-3 py-1 border ${
                    analysisMode === 'enhanced' 
                      ? 'bg-primary-700 text-white border-primary-700' 
                      : 'bg-neutral-100 text-neutral-700 border-neutral-300'
                  }`}>
                    {analysisMode === 'enhanced' ? 'Enhanced AI Analysis' : 'Normal'}
                  </span>
                </div>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-accent-terra/10 border-2 border-accent-terra p-4 mb-6">
                <p className="body-default text-accent-terra font-medium">{error}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setSelectedPatient(null);
                  setAnalysisMode('enhanced');
                  openPatientSelection();
                }}
                className="flex-1 px-6 py-4 border-2 border-neutral-300 text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 label-uppercase transition-colors"
              >
                Change Patient
              </button>
              <button
                onClick={handleStartView}
                className="flex-1 px-6 py-4 bg-primary-700 hover:bg-primary-900 text-white label-uppercase transition-colors hover-lift"
              >
                Start View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Webcam view - shown after clicking Start View */}
      {selectedPatient && viewStarted && (
        <div className="min-h-screen bg-neutral-50 flex flex-col">
          {/* Header Info Bar */}
          <div className="bg-surface border-b-2 border-neutral-950 p-6">
            <div className="container mx-auto flex items-center justify-between">
              <div className="flex items-center gap-6">
                <img
                  src={selectedPatient.photo_url}
                  alt={selectedPatient.name}
                  className="w-16 h-16 object-cover rounded-lg"
                />
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-xl font-light text-neutral-950">{selectedPatient.name}</h3>
                    <span className="label-uppercase bg-primary-700 text-white px-2 py-1 text-xs">
                      {selectedPatient.patient_id}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-600">
                    {selectedPatient.age}y/o • {selectedPatient.gender} • {selectedPatient.condition}
                  </p>
                </div>
              </div>
              <button
                onClick={stopStreaming}
                className="px-6 py-3 bg-accent-terra hover:bg-accent-terra/80 text-white label-uppercase transition-colors"
              >
                Stop View
              </button>
            </div>
          </div>

          {/* Main Content - Split Layout */}
          <div className="flex-1 flex overflow-hidden">
            {/* Left Half - Video Display */}
            <div className="w-1/2 relative bg-neutral-950 border-r-2 border-neutral-950">
              <video
                ref={videoRef}
                className="w-full h-full object-cover"
                style={{ transform: 'scaleX(-1)' }}
                autoPlay
                muted
                playsInline
              />

              {/* Status Overlay */}
              <div className="absolute top-4 right-4 px-4 py-2 bg-neutral-950/90">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 ${
                    isStreaming ? 'bg-accent-terra animate-pulse' : 'bg-neutral-500'
                  }`} />
                  <span className="label-uppercase text-white">
                    {isStreaming ? 'LIVE' : isConnecting ? 'CONNECTING' : 'OFFLINE'}
                  </span>
                </div>
              </div>

              {/* FPS Counter */}
              {isStreaming && (
                <div className="absolute top-4 left-4 px-3 py-2 bg-neutral-950/90 border border-primary-700">
                  <span className="label-uppercase text-primary-400">
                    {fps} FPS
                  </span>
                </div>
              )}
            </div>

            {/* Right Half - Reports Panel */}
            <div className="w-1/2 bg-neutral-50 p-6 flex flex-col gap-6 overflow-y-auto">
              {/* Reports Card - Combined */}
              <div className="bg-white border border-neutral-200 rounded-lg p-6">
                {/* Generate Report Button */}
                <button
                  className="w-full px-6 py-3 bg-primary-700 hover:bg-primary-900 text-white label-uppercase transition-colors hover-lift rounded-lg mb-6"
                  onClick={() => {
                    // TODO: Implement report generation
                    console.log('Generate report for patient:', selectedPatient.patient_id);
                  }}
                >
                  Generate Report
                </button>

                {/* Past Reports Section */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="heading-section text-neutral-950">Past Reports</h3>
                    <span className="label-uppercase bg-neutral-100 text-neutral-700 px-2 py-1 text-xs">
                      0 Reports
                    </span>
                  </div>

                  {/* Empty State */}
                  <div className="text-center py-12 border-2 border-dashed border-neutral-200 rounded-lg">
                    <svg className="w-12 h-12 mx-auto text-neutral-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                    </svg>
                    <p className="text-sm text-neutral-500 mb-2">No reports generated yet</p>
                    <p className="text-xs text-neutral-400">
                      Generate your first report to see it here
                    </p>
                  </div>

                  {/* Future: List of past reports will go here */}
                </div>
              </div>

              {/* Voice Notes Card */}
              <div className="bg-white border border-neutral-200 rounded-lg p-4">
                {/* Microphone Controls */}
                <div className="flex items-center justify-center gap-4">
                  {/* Mic Status Text */}
                  <div className="flex-1 text-right">
                    <span className={`text-sm font-medium ${isMicActive ? 'text-accent-terra' : 'text-neutral-500'}`}>
                      {isMicActive ? 'Recording...' : 'Ready'}
                    </span>
                  </div>

                  {/* Microphone Button */}
                  <button
                    onClick={() => {
                      setIsMicActive(!isMicActive);
                      // TODO: Implement voice recording
                      console.log('Microphone toggled:', !isMicActive);
                    }}
                    className={`relative w-14 h-14 rounded-full transition-all duration-200 ${
                      isMicActive 
                        ? 'bg-accent-terra hover:bg-accent-terra/90 scale-110 shadow-lg' 
                        : 'bg-primary-700 hover:bg-primary-900 shadow-md hover:scale-105'
                    }`}
                  >
                    {isMicActive ? (
                      // Recording - Stop icon
                      <svg className="w-6 h-6 text-white mx-auto" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="6" width="12" height="12" rx="2" />
                      </svg>
                    ) : (
                      // Not recording - Microphone icon
                      <svg className="w-6 h-6 text-white mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                      </svg>
                    )}
                    
                    {/* Pulse animation when active */}
                    {isMicActive && (
                      <span className="absolute inset-0 rounded-full bg-accent-terra animate-ping opacity-75" />
                    )}
                  </button>

                  {/* Hint Text */}
                  <div className="flex-1">
                    <span className="text-sm text-neutral-500">
                      {isMicActive ? 'Tap to stop' : 'Tap to record'}
                    </span>
                  </div>
                </div>

                {/* Recording indicator */}
                {isMicActive && (
                  <div className="mt-3">
                    <div className="flex items-center gap-3 px-4 py-2 bg-accent-terra/10 border border-accent-terra/30 rounded-lg">
                      <div className="flex gap-1">
                        <div className="w-1 h-3 bg-accent-terra rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                        <div className="w-1 h-3 bg-accent-terra rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                        <div className="w-1 h-3 bg-accent-terra rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-xs font-medium text-accent-terra">Recording audio note</span>
                      <div className="ml-auto text-xs font-mono text-accent-terra">00:00</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}
    </div>
  );
}

