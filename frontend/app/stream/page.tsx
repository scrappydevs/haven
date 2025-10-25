'use client';

import { useEffect, useRef, useState } from 'react';
import PatientSearchModal from '@/components/PatientSearchModal';
import MonitoringConditionSelector from '@/components/MonitoringConditionSelector';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

export default function StreamPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const captureCleanupRef = useRef<(() => void) | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [tempPatient, setTempPatient] = useState<Patient | null>(null);  // Temporary until conditions confirmed
  const [monitoringConditions, setMonitoringConditions] = useState<string[]>([]);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [showConditionSelector, setShowConditionSelector] = useState(false);
  const [activeStreams, setActiveStreams] = useState<string[]>([]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [fps, setFps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      stopStreaming();
    };
  }, []);

  // Fetch active streams and open patient selection modal
  const openPatientSelection = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/streams/active`);
      const data = await res.json();
      setActiveStreams(data.active_streams || []);
      setShowPatientModal(true);
    } catch (error) {
      console.error('Error fetching active streams:', error);
      setShowPatientModal(true);  // Show modal anyway
    }
  };

  const startStreaming = async () => {
    // Check if patient is selected
    if (!selectedPatient) {
      setError('Please select a patient first');
      return;
    }

    // Prevent double-start
    if (isStreaming || isConnecting) {
      console.log('⚠️ Already streaming or connecting');
      return;
    }

    try {
      setIsConnecting(true);
      setError(null);

      // Stop any existing streams first
      if (captureCleanupRef.current) {
        captureCleanupRef.current();
        captureCleanupRef.current = null;
      }

      // Request webcam access
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

      // Set video source and wait for it to be ready
      const video = videoRef.current;
      if (!video) {
        throw new Error('Video element not found');
      }

      video.srcObject = stream;

      // Wait for video metadata to load before playing
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Video load timeout')), 5000);

        video.onloadedmetadata = () => {
          clearTimeout(timeout);
          console.log('✅ Video metadata loaded');
          resolve();
        };
      });

      // Now play the video
      try {
        await video.play();
        console.log('✅ Video playing');
      } catch (playError) {
        console.error('Video play error:', playError);
        throw new Error('Failed to play video');
      }

      // Connect to patient-specific WebSocket
      const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + `/ws/stream/${selectedPatient.patient_id}`;
      console.log(`🔌 Connecting to WebSocket for patient ${selectedPatient.patient_id}:`, wsUrl);

      const ws = new WebSocket(wsUrl || `ws://localhost:8000/ws/stream/${selectedPatient.patient_id}`);
      wsRef.current = ws;

      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          setError('Connection timeout. Is the backend running on port 8000?');
          setIsConnecting(false);
        }
      }, 5000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log('✅ Connected to WebSocket server');

        // Send initial handshake with monitoring conditions
        ws.send(JSON.stringify({
          type: 'handshake',
          monitoring_conditions: monitoringConditions
        }));
        console.log(`📋 Sent monitoring conditions:`, monitoringConditions);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'connected') {
          console.log('✅ Handshake confirmed, starting stream');
          setIsStreaming(true);
          setIsConnecting(false);

          // Start capturing and sending frames
          const cleanup = startCapture();
          captureCleanupRef.current = cleanup;
        }
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        console.log('❌ Disconnected from server. Code:', event.code, 'Reason:', event.reason);
        setIsStreaming(false);
        setIsConnecting(false);

        if (event.code === 1006) {
          setError('Connection failed. Make sure backend is running: cd backend && uvicorn app.main:app --reload');
        }
      };

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        console.error('❌ WebSocket error:', error);
        setError('Failed to connect to server. Make sure backend is running on port 8000.');
        setIsConnecting(false);
      };

    } catch (err: any) {
      console.error('Error starting stream:', err);
      setError(err.message || 'Could not access webcam. Please allow camera permissions.');
      setIsConnecting(false);

      // Cleanup on error
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
        // Downscale to 640x360 for streaming performance (4x less data)
        const targetWidth = 640;
        const targetHeight = 360;

        if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
          canvas.width = targetWidth;
          canvas.height = targetHeight;
          console.log(`📐 Canvas sized to ${canvas.width}x${canvas.height} (downscaled)`);
        }

        // Draw current video frame to canvas (scaled down)
        ctx.drawImage(video, 0, 0, targetWidth, targetHeight);

        // Convert canvas to base64 JPEG (lower quality for streaming)
        const frameData = canvas.toDataURL('image/jpeg', 0.7);

        // Send to backend via WebSocket
        wsRef.current.send(JSON.stringify({
          type: 'frame',
          frame: frameData
        }));

        // Log every 30th frame (once per second at 30fps)
        if (frameCount % 30 === 0) {
          console.log('📤 Sent frame to backend, size:', frameData.length, 'bytes');
        }

        // Update FPS counter
        frameCount++;
        const now = Date.now();
        if (now - lastFpsUpdate >= 1000) {
          setFps(frameCount);
          frameCount = 0;
          lastFpsUpdate = now;
        }

        // Capture next frame (30 FPS ≈ 33ms interval)
        timeoutId = setTimeout(captureFrame, 33);
      } catch (error) {
        console.error('❌ Error in capture frame:', error);
        isActive = false;
      }
    };

    console.log('▶️ Starting frame capture');
    captureFrame();

    // Return cleanup function
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

    // Stop frame capture first
    if (captureCleanupRef.current) {
      captureCleanupRef.current();
      captureCleanupRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop all media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('Stopped track:', track.kind);
      });
      streamRef.current = null;
    }

    // Clear video element
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
    setIsConnecting(false);
    setFps(0);
    console.log('✅ Stream stopped');
  };

  return (
    <div className="min-h-screen bg-neutral-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 border-b-2 border-neutral-950 pb-4">
          <h1 className="heading-page text-neutral-950 mb-2">
            Live Stream
          </h1>
          <p className="body-large text-neutral-700">
            Stream your webcam to the dashboard for live CV analysis
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-accent-terra/10 border-2 border-accent-terra p-4 mb-6">
            <p className="body-default text-accent-terra font-medium">{error}</p>
          </div>
        )}

        {/* Selected Patient Card */}
        {selectedPatient ? (
          <div className="bg-white border-2 border-neutral-950 p-6 mb-6 hover-lift">
            <div className="flex items-center gap-6">
              <img
                src={selectedPatient.photo_url}
                alt={selectedPatient.name}
                className="w-20 h-20 object-cover border-2 border-neutral-950"
              />
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="heading-section text-neutral-950">{selectedPatient.name}</h3>
                  <span className="label-uppercase bg-primary-700 text-white px-3 py-1">
                    {selectedPatient.patient_id}
                  </span>
                </div>
                <p className="body-default text-neutral-700 mb-1">
                  {selectedPatient.age}y/o • {selectedPatient.gender}
                </p>
                <p className="body-default text-neutral-950 font-medium">{selectedPatient.condition}</p>
                {monitoringConditions.length > 0 && (
                  <div className="flex items-center gap-2 mt-3">
                    <span className="label-uppercase text-neutral-700">Monitoring:</span>
                    {monitoringConditions.map(condition => (
                      <span key={condition} className="label-uppercase bg-primary-100 text-primary-950 px-2 py-1 border border-primary-700">
                        {condition}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {!isStreaming && (
                <button
                  onClick={openPatientSelection}
                  className="px-6 py-3 bg-neutral-950 hover:bg-neutral-700 text-white label-uppercase transition-colors"
                >
                  Change Patient
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white border-2 border-neutral-950 p-12 mb-6 text-center">
            <div className="mb-6">
              <div className="w-24 h-24 mx-auto bg-neutral-100 border-2 border-neutral-950 flex items-center justify-center">
                <span className="heading-section text-neutral-500">?</span>
              </div>
            </div>
            <h3 className="heading-section text-neutral-950 mb-2">No Patient Selected</h3>
            <p className="body-default text-neutral-700 mb-6">Select a patient to start streaming</p>
            <button
              onClick={openPatientSelection}
              className="px-8 py-4 bg-primary-700 hover:bg-primary-900 text-white label-uppercase transition-colors hover-lift"
            >
              Select Patient
            </button>
          </div>
        )}

        {/* Video Preview */}
        <div className="bg-white border-2 border-neutral-950 p-6 mb-6">
          <div className="relative aspect-video bg-neutral-950 overflow-hidden mb-6 border-2 border-neutral-950">
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
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
                  {isStreaming ? 'LIVE' : 'OFFLINE'}
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

          {/* Controls */}
          <div className="flex gap-4">
            {!isStreaming && !isConnecting ? (
              <button
                onClick={startStreaming}
                disabled={!selectedPatient}
                className={`flex-1 label-uppercase py-4 transition-all border-2 ${
                  selectedPatient
                    ? 'bg-primary-700 hover:bg-primary-900 text-white border-primary-700 hover:border-primary-900 cursor-pointer hover-lift'
                    : 'bg-neutral-100 text-neutral-400 border-neutral-200 cursor-not-allowed'
                }`}
              >
                Start Streaming {selectedPatient ? `as ${selectedPatient.patient_id}` : ''}
              </button>
            ) : isConnecting ? (
              <button
                disabled
                className="flex-1 bg-neutral-700 text-white label-uppercase py-4 border-2 border-neutral-700 opacity-75 cursor-not-allowed"
              >
                Connecting...
              </button>
            ) : (
              <button
                onClick={stopStreaming}
                className="flex-1 bg-accent-terra hover:bg-accent-terra/80 text-white label-uppercase py-4 border-2 border-accent-terra transition-all hover-lift"
              >
                Stop Streaming
              </button>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white border-2 border-neutral-950 p-8">
          <h2 className="heading-section text-neutral-950 mb-6 border-b-2 border-neutral-950 pb-3">How to Use</h2>
          <ol className="space-y-4 body-default text-neutral-950">
            <li className="flex gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">01</span>
              <span>Click &quot;Start Streaming&quot; button above</span>
            </li>
            <li className="flex gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">02</span>
              <span>Allow camera permissions when prompted</span>
            </li>
            <li className="flex gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">03</span>
              <span>On another computer, open the dashboard</span>
            </li>
            <li className="flex gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">04</span>
              <span>Look for your patient in the live feed section</span>
            </li>
            <li className="flex gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">05</span>
              <span>Try rubbing your face to simulate CRS → Alert fires!</span>
            </li>
          </ol>

          <div className="mt-6 p-4 bg-primary-100 border-l-4 border-primary-700">
            <p className="body-default text-neutral-950">
              <span className="font-semibold">Note:</span> Make sure both computers are on the same network and backend is running!
            </p>
          </div>
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Patient Search Modal (Step 1) */}
      <PatientSearchModal
        isOpen={showPatientModal}
        onClose={() => setShowPatientModal(false)}
        onSelect={(patient) => {
          setTempPatient(patient);
          setShowPatientModal(false);
          setShowConditionSelector(true);
        }}
        activeStreams={activeStreams}
      />

      {/* Monitoring Condition Selector Modal (Step 2) */}
      {showConditionSelector && tempPatient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/80"
            onClick={() => setShowConditionSelector(false)}
          />

          {/* Modal */}
          <div className="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <MonitoringConditionSelector
              patient={tempPatient}
              onConfirm={(conditions) => {
                setSelectedPatient(tempPatient);
                setMonitoringConditions(conditions);
                setShowConditionSelector(false);

                // Save monitoring config to localStorage for dashboard to read
                if (tempPatient) {
                  localStorage.setItem(
                    `monitoring-${tempPatient.patient_id}`,
                    JSON.stringify(conditions)
                  );
                  console.log(`💾 Saved monitoring config for ${tempPatient.patient_id}:`, conditions);
                }

                setTempPatient(null);
                console.log(`✅ Selected patient ${tempPatient.patient_id} with conditions:`, conditions);
              }}
              onBack={() => {
                setShowConditionSelector(false);
                setShowPatientModal(true);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

