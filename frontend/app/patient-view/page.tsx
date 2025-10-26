'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
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
  const [showAIAnimation, setShowAIAnimation] = useState(false);

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

          {/* Main Content - Full Screen Video/Animation */}
          <div className="flex-1 relative overflow-hidden p-6">
            {/* Video Display */}
            {!showAIAnimation && (
              <div className="absolute inset-6 bg-neutral-950 rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }}
                  autoPlay
                  muted
                  playsInline
                />

                {/* Status Overlay */}
                <div className="absolute top-4 right-4 px-4 py-2 bg-neutral-950/90 rounded">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      isStreaming ? 'bg-accent-terra animate-pulse' : 'bg-neutral-500'
                    }`} />
                    <span className="label-uppercase text-white text-xs">
                      {isStreaming ? 'LIVE' : isConnecting ? 'CONNECTING' : 'OFFLINE'}
                    </span>
                  </div>
                </div>

                {/* FPS Counter */}
                {isStreaming && (
                  <div className="absolute top-4 left-4 px-3 py-2 bg-neutral-950/90 border border-neutral-700 rounded">
                    <span className="label-uppercase text-neutral-400 text-xs">
                      {fps} FPS
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* AI Animation View */}
            {showAIAnimation && (
              <div className="absolute inset-6 bg-gradient-to-br from-neutral-50 to-neutral-100 rounded-lg overflow-hidden flex items-center justify-center">
                <div className="text-center">
                  {/* Central Orb with Pulse */}
                  <motion.div
                    className="relative mx-auto mb-8"
                    style={{ width: 200, height: 200 }}
                  >
                    {/* Outer pulse rings */}
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-neutral-400"
                      animate={{
                        scale: [1, 1.5, 1],
                        opacity: [0.5, 0, 0.5]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    />
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-neutral-400"
                      animate={{
                        scale: [1, 1.5, 1],
                        opacity: [0.5, 0, 0.5]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.5
                      }}
                    />

                    {/* Central circle */}
                    <motion.div
                      className="absolute inset-0 rounded-full bg-white border-4 border-neutral-300 flex items-center justify-center shadow-xl"
                      animate={{
                        scale: [1, 1.05, 1]
                      }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <svg className="w-20 h-20 text-neutral-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                      </svg>
                    </motion.div>
                  </motion.div>

                  {/* Sound Wave Bars */}
                  <div className="flex items-center justify-center gap-1.5 mb-6">
                    {[...Array(12)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="w-1.5 bg-neutral-600 rounded-full"
                        animate={{
                          height: [20, 60, 20]
                        }}
                        transition={{
                          duration: 0.8,
                          repeat: Infinity,
                          ease: "easeInOut",
                          delay: i * 0.1
                        }}
                      />
                    ))}
                  </div>

                  {/* Status Text */}
                  <motion.p
                    className="text-xl font-light text-neutral-700"
                    animate={{
                      opacity: [1, 0.6, 1]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    {isMicActive ? 'Listening...' : 'AI Voice Agent Ready'}
                  </motion.p>
                </div>
              </div>
            )}

            {/* Bottom AI Voice Agent Card */}
            <div className="absolute bottom-6 left-6 right-6 z-10">
              <motion.div
                onClick={() => setShowAIAnimation(!showAIAnimation)}
                className="bg-white border border-neutral-300 rounded-lg shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="px-6 py-3 flex items-center justify-between">
                  {/* Left: Agent Info */}
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-neutral-100 flex items-center justify-center">
                      <svg className="w-5 h-5 text-neutral-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-neutral-950">AI Voice Agent</p>
                      <p className="text-xs text-neutral-500">
                        {showAIAnimation ? 'Click to return to video' : 'Click to activate voice mode'}
                      </p>
                    </div>
                  </div>

                  {/* Center: Status Indicator */}
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      isMicActive ? 'bg-accent-terra animate-pulse' : 'bg-neutral-400'
                    }`} />
                    <span className="text-xs text-neutral-600">
                      {isMicActive ? 'Active' : 'Ready'}
                    </span>
                  </div>

                  {/* Right: Microphone Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent card click when clicking mic
                      setIsMicActive(!isMicActive);
                      console.log('Microphone toggled:', !isMicActive);
                    }}
                    className={`w-12 h-12 rounded-full transition-all duration-200 flex items-center justify-center ${
                      isMicActive
                        ? 'bg-accent-terra hover:bg-accent-terra/90 shadow-lg'
                        : 'bg-neutral-200 hover:bg-neutral-300'
                    }`}
                  >
                    {isMicActive ? (
                      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="6" width="12" height="12" rx="2" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-neutral-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                      </svg>
                    )}
                  </button>
                </div>
              </motion.div>
            </div>
          </div>

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}
    </div>
  );
}

