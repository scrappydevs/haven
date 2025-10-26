'use client';

import { useEffect, useRef, useState } from 'react';
import PatientSearchModal from '@/components/PatientSearchModal';
import AnalysisModeSelector, { AnalysisMode } from '@/components/AnalysisModeSelector';
import AIVoiceAnimation from '@/components/AIVoiceAnimation';
import { getApiUrl, getWsUrl } from '@/lib/api';
import { LiveKitRoom, useVoiceAssistant, BarVisualizer, RoomAudioRenderer } from '@livekit/components-react';
import '@livekit/components-styles';

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
  const isConnectingRef = useRef<boolean>(false); // Prevent duplicate connections

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [tempPatient, setTempPatient] = useState<Patient | null>(null);  // Temporary until mode confirmed
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('enhanced');
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [activeStreams, setActiveStreams] = useState<string[]>([]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [fps, setFps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Haven voice agent state
  const [isListeningForWakeWord, setIsListeningForWakeWord] = useState(false);
  const [havenActive, setHavenActive] = useState(false);
  const [havenTranscript, setHavenTranscript] = useState<string>('');
  const [havenRoomData, setHavenRoomData] = useState<{token: string, url: string, room_name: string, session_id: string} | null>(null);
  const [voiceAssistantActive, setVoiceAssistantActive] = useState(false);
  const recognitionRef = useRef<any>(null);
  const isStartingRecognitionRef = useRef<boolean>(false);
  const restartTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup on TRUE unmount (page navigation away)
      // Check refs to see if there's actually something to clean up
      if (wsRef.current || streamRef.current) {
        console.log('🧹 Component unmounting - cleaning up stream');
        // Direct cleanup without calling stopStreaming to avoid state updates during unmount
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
  }, []); // Empty deps - only run on mount/unmount

  // Fetch active streams and open patient selection modal
  const openPatientSelection = async () => {
    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/streams/active`);
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

    // Prevent double-start (using ref to survive React strict mode double-render)
    if (isStreaming || isConnecting || isConnectingRef.current) {
      console.log('⚠️ Already streaming or connecting (prevented duplicate)');
      return;
    }

    // Set connecting flag immediately (ref-based, survives re-renders)
    isConnectingRef.current = true;

    try {
      setIsConnecting(true);
      setError(null);

      // Stop any existing streams first
      if (captureCleanupRef.current) {
        captureCleanupRef.current();
        captureCleanupRef.current = null;
      }

      // Close any existing WebSocket connections
      if (wsRef.current) {
        console.log('⚠️  Closing existing WebSocket before starting new one');
        try {
          wsRef.current.close();
        } catch (e) {
          console.log('   (Error closing old WS, continuing anyway)');
        }
        wsRef.current = null;
      }

      // Check current permissions status
      console.log('🔍 Checking current media permissions...');
      try {
        const videoPermission = await navigator.permissions.query({ name: 'camera' as PermissionName });
        const audioPermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        console.log('📊 Permission status:', {
          camera: videoPermission.state,
          microphone: audioPermission.state
        });

        // If microphone is denied, show clear error
        if (audioPermission.state === 'denied') {
          throw new Error('Microphone permission is DENIED in browser settings. Please enable microphone access in your browser settings and refresh the page.');
        }
      } catch (e: any) {
        if (e.message?.includes('DENIED')) {
          throw e; // Re-throw if it's our custom error
        }
        console.log('⚠️ Could not query permissions (may not be supported):', e);
      }

      // List available devices
      console.log('🔍 Checking available media devices...');
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        const audioDevices = devices.filter(d => d.kind === 'audioinput');
        console.log('📊 Available devices:', {
          cameras: videoDevices.length,
          microphones: audioDevices.length,
          videoDevices: videoDevices.map(d => ({ label: d.label || 'Unknown', id: d.deviceId })),
          audioDevices: audioDevices.map(d => ({ label: d.label || 'Unknown', id: d.deviceId }))
        });

        if (audioDevices.length === 0) {
          throw new Error('No microphone detected on this device. Please connect a microphone and refresh the page.');
        }
      } catch (e) {
        console.error('❌ Device enumeration error:', e);
        throw e;
      }

      // Request video first
      console.log('📹 Step 1: Requesting webcam access...');
      let videoStream: MediaStream;
      try {
        videoStream = await Promise.race([
          navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              frameRate: { ideal: 30 }
            }
          }),
          new Promise<MediaStream>((_, reject) =>
            setTimeout(() => reject(new Error('Video request timed out after 10 seconds')), 10000)
          )
        ]);
        console.log('✅ Webcam access granted');
      } catch (error: any) {
        console.error('❌ Video request failed:', error);
        throw new Error(`Failed to access camera: ${error.message}`);
      }

      // Request audio separately
      console.log('🎤 Step 2: Requesting microphone access...');
      let audioStream: MediaStream;
      try {
        audioStream = await Promise.race([
          navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
            }
          }),
          new Promise<MediaStream>((_, reject) =>
            setTimeout(() => reject(new Error('Audio request timed out after 10 seconds')), 10000)
          )
        ]);
        console.log('✅ Microphone access granted');
      } catch (error: any) {
        console.error('❌ Audio request failed:', error);
        // Clean up video stream
        videoStream.getTracks().forEach(track => track.stop());
        throw new Error(`Failed to access microphone: ${error.message}`);
      }

      // Combine both streams
      console.log('🔗 Combining video and audio streams...');
      const combinedStream = new MediaStream([
        ...videoStream.getVideoTracks(),
        ...audioStream.getAudioTracks()
      ]);

      streamRef.current = combinedStream;
      console.log('✅ Combined stream ready', {
        videoTracks: combinedStream.getVideoTracks().length,
        audioTracks: combinedStream.getAudioTracks().length,
        videoSettings: combinedStream.getVideoTracks()[0]?.getSettings(),
        audioSettings: combinedStream.getAudioTracks()[0]?.getSettings()
      });

      // Set video source and wait for it to be ready
      const video = videoRef.current;
      if (!video) {
        throw new Error('Video element not found');
      }

      video.srcObject = combinedStream;

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
      const wsUrl = getWsUrl(`/ws/stream/${selectedPatient.patient_id}`);
      console.log(`🔌 Connecting to WebSocket for patient ${selectedPatient.patient_id}:`, wsUrl);
      console.log(`   Current wsRef state:`, wsRef.current ? 'HAS OLD CONNECTION' : 'clean');
      console.log(`   Browser supports WebSocket:`, 'WebSocket' in window);

      const ws = new WebSocket(wsUrl);
      console.log(`   WebSocket created, initial readyState:`, ws.readyState, '(0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)');
      wsRef.current = ws;

      // Check state after a tiny delay to see if it failed immediately
      setTimeout(() => {
        console.log(`   WebSocket state after 10ms:`, ws.readyState);
        if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
          console.error('❌ WebSocket closed immediately after creation - this suggests browser security blocking');
        }
      }, 10);

      // Set a connection timeout
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
        console.log('   readyState:', ws.readyState);
        console.log('   url:', ws.url);

        // Send initial handshake with analysis mode
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
          isConnectingRef.current = false; // Clear connecting flag

          if (data.warning) {
            console.warn('⚠️ WebSocket warning:', data.warning);
          }

          // Start capturing and sending frames
          const cleanup = startCapture();
          captureCleanupRef.current = cleanup;
        }
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        
        // Capture state before updating (use REF for accurate state, not async state)
        const hadConnection = isStreaming;
        const wasAttemptingConnection = isConnecting || isConnectingRef.current;
        
        console.log('❌ Disconnected from server. Code:', event.code, 'Reason:', event.reason, 
                    'hadConnection:', hadConnection, 'wasAttempting:', wasAttemptingConnection,
                    'connectingRef:', isConnectingRef.current);
        
        setIsStreaming(false);
        setIsConnecting(false);
        isConnectingRef.current = false; // Clear connecting flag

        // Ignore transient failures during initial connection (React dev mode double-render issue)
        if (!hadConnection && !wasAttemptingConnection && event.code === 1006) {
          console.warn('⚠️  Ignoring transient connection close (likely React dev mode duplicate)');
          return;
        }

        // Show errors only for real connection failures
        if (event.reason) {
          setError(event.reason);
        } else if (event.code === 4090) {
          setError('This patient already has an active stream. Please stop the other stream before starting a new one.');
        } else if (event.code === 1006 && wasAttemptingConnection) {
          setError('Connection failed. Make sure backend is running: cd backend && python3 main.py');
        }
      };

      ws.onerror = (event) => {
        // Don't clear timeout yet - connection might still succeed
        // (React dev mode or browser can cause initial failed attempts)
        const errorEvent = event as ErrorEvent & {
          message?: string;
          reason?: string;
          error?: unknown;
        };

        const detailedMessage =
          (errorEvent instanceof ErrorEvent && errorEvent.message) ||
          errorEvent.message ||
          (errorEvent.error instanceof Error && errorEvent.error.message) ||
          (typeof errorEvent.reason === 'string' ? errorEvent.reason : undefined);

        console.warn('⚠️  WebSocket error (may be transient):', detailedMessage || 'unknown issue', {
          event,
          url: ws.url,
          readyState: ws.readyState,
        });

        // Only show error and cleanup if we're not already connected
        // Wait for onclose to handle cleanup
      };

    } catch (err: any) {
      console.error('Error starting stream:', err);
      setError(err.message || 'Could not access webcam. Please allow camera permissions.');
      setIsConnecting(false);
      isConnectingRef.current = false; // Clear connecting flag

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
    isConnectingRef.current = false; // Clear connecting flag
    setFps(0);
    console.log('✅ Stream stopped');
  };

  // Wake word detection and Haven voice agent functions
  const startWakeWordListening = () => {
    console.log('🔍 startWakeWordListening called', {
      hasPatient: !!selectedPatient,
      isStreaming,
      havenActive,
      isStarting: isStartingRecognitionRef.current,
      hasRecognition: !!recognitionRef.current
    });

    if (!selectedPatient) {
      console.warn('⚠️ Cannot start wake word listening without selected patient');
      return;
    }

    // Prevent starting if already starting or already running
    if (isStartingRecognitionRef.current || recognitionRef.current) {
      console.log('⚠️ Wake word listening already active, skipping start');
      return;
    }

    isStartingRecognitionRef.current = true;
    console.log('✅ Starting wake word recognition...');

    // Check for Web Speech API support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error('❌ Speech Recognition not supported in this browser');
      setError('Wake word detection not supported in your browser. Please use Chrome or Edge.');
      isStartingRecognitionRef.current = false;
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('🎤 Wake word listening started');
      console.log('🎙️ Microphone should now be active - try speaking');
      setIsListeningForWakeWord(true);
      isStartingRecognitionRef.current = false;
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join('')
        .toLowerCase();

      const isFinal = event.results[event.results.length - 1].isFinal;
      console.log(`🎤 Heard (${isFinal ? 'FINAL' : 'interim'}):`, transcript);

      // Check for wake word "hey haven"
      if (transcript.includes('hey haven') || transcript.includes('hey heaven')) {
        console.log('🛡️ Wake word detected! Stopping recognition and starting Haven session...');
        recognition.stop();
        startHavenSession();
      }
    };

    recognition.onerror = (event: any) => {
      console.error('❌ Speech recognition error:', event.error);
      isStartingRecognitionRef.current = false;

      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow microphone access for wake word detection.');
        setIsListeningForWakeWord(false);
      } else if (event.error === 'no-speech') {
        // No speech detected is normal, just restart
        console.log('ℹ️ No speech detected, will restart');
      } else {
        console.warn('⚠️ Recognition error, will attempt restart');
      }
    };

    recognition.onend = () => {
      console.log('🛑 Wake word recognition ended');
      isStartingRecognitionRef.current = false;

      // Clear any pending restart
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current);
      }

      // Restart listening if not in Haven session and streaming is active
      if (!havenActive && isStreaming && selectedPatient) {
        console.log('🔄 Scheduling wake word restart in 1 second...');
        restartTimeoutRef.current = setTimeout(() => {
          startWakeWordListening();
        }, 1000); // Wait 1 second before restarting to prevent rapid loops
      } else {
        console.log('🛑 Wake word listening stopped (conditions not met for restart)');
        setIsListeningForWakeWord(false);
      }
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
    } catch (err) {
      console.error('❌ Failed to start wake word listening:', err);
      setError('Failed to start microphone for wake word detection');
      isStartingRecognitionRef.current = false;
    }
  };

  const stopWakeWordListening = () => {
    console.log('🛑 Stopping wake word listening');

    // Clear any pending restart
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        console.warn('Error stopping recognition:', err);
      }
      recognitionRef.current = null;
    }

    isStartingRecognitionRef.current = false;
    setIsListeningForWakeWord(false);
  };

  const startHavenSession = async () => {
    if (!selectedPatient) return;

    try {
      console.log('🛡️ Starting Haven voice session...');
      setHavenActive(true);
      setHavenTranscript('Connecting to Haven AI...');

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/haven/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: selectedPatient.patient_id })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      console.log('✅ Haven session created:', data.room_name);

      // Store room data for LiveKit connection
      setHavenRoomData({
        token: data.token,
        url: data.url,
        room_name: data.room_name,
        session_id: data.session_id
      });

      // Initial transcript - will be updated by voice assistant component
      setHavenTranscript('Initializing voice connection...');

    } catch (err: any) {
      console.error('❌ Failed to start Haven session:', err);
      setError('Failed to start voice assistant: ' + err.message);
      setHavenActive(false);
      setHavenTranscript('');
      // Restart wake word listening
      startWakeWordListening();
    }
  };

  const endHavenSession = async () => {
    console.log('🛡️ Ending Haven session');

    // TODO: Get conversation summary from LiveKit agent
    // For now, create a mock summary
    if (havenRoomData && selectedPatient) {
      try {
        const apiUrl = getApiUrl();

        // Mock conversation summary (in production, this would come from the agent)
        const mockSummary = {
          patient_id: selectedPatient.patient_id,
          session_id: havenRoomData.session_id,
          conversation_summary: {
            full_transcript_text: havenTranscript,
            extracted_info: {
              symptom_description: "Patient reported concern",
              body_location: null,
              pain_level: null,
              duration: null
            }
          }
        };

        console.log('💾 Saving Haven conversation summary...');
        const response = await fetch(`${apiUrl}/api/haven/conversation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(mockSummary)
        });

        const result = await response.json();
        if (result.success) {
          console.log('✅ Haven conversation saved, alert created:', result.alert_id);
        } else {
          console.warn('⚠️ Failed to save conversation:', result.error);
        }
      } catch (err) {
        console.error('❌ Error saving Haven conversation:', err);
      }
    }

    setHavenActive(false);
    setHavenTranscript('');
    setHavenRoomData(null);

    // Restart wake word listening
    if (isStreaming && selectedPatient) {
      startWakeWordListening();
    }
  };

  // Wake word listening effect
  useEffect(() => {
    if (isStreaming && selectedPatient && !havenActive) {
      // Start wake word listening when streaming starts
      startWakeWordListening();
    } else if (!isStreaming || !selectedPatient) {
      // Stop wake word listening when streaming stops
      stopWakeWordListening();
    }

    return () => {
      // Cleanup: stop listening and clear timeouts
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current);
        restartTimeoutRef.current = null;
      }
      stopWakeWordListening();
    };
  }, [isStreaming, selectedPatient, havenActive]);

  // Haven Voice Assistant Component
  function HavenVoiceAssistant() {
    const { state, audioTrack } = useVoiceAssistant();
    const lastStateRef = useRef<string>('');

    useEffect(() => {
      // Only update if state actually changed and add debouncing
      if (state !== lastStateRef.current) {
        lastStateRef.current = state;

        console.log('🎤 Haven voice assistant state:', state);

        // Update voice assistant active state for animation
        setVoiceAssistantActive(state === 'listening' || state === 'speaking' || state === 'thinking');

        // Update transcript based on voice assistant state with slight delay to avoid flicker
        const timer = setTimeout(() => {
          if (state === 'connecting') {
            setHavenTranscript('Connecting to Haven AI...');
          } else if (state === 'listening') {
            setHavenTranscript('Haven AI is listening');
          } else if (state === 'thinking') {
            setHavenTranscript('Haven AI is processing');
          } else if (state === 'speaking') {
            setHavenTranscript('Haven AI is speaking');
          } else if (state === 'initializing') {
            setHavenTranscript('Haven AI is initializing...');
          } else {
            // Handle any other states (disconnected, etc)
            setHavenTranscript('Haven AI connected');
          }
        }, 100);

        return () => clearTimeout(timer);
      }
    }, [state]);

    return (
      <>
        <RoomAudioRenderer />
        {audioTrack && (
          <div className="flex justify-center mb-4">
            <BarVisualizer state={state} barCount={5} trackRef={audioTrack} className="w-full" />
          </div>
        )}
      </>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header with Navigation */}
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
                className="px-6 py-2 label-uppercase text-xs text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50 transition-colors"
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
                className="px-6 py-2 label-uppercase text-xs text-neutral-950 border-b-2 border-primary-700 hover:bg-neutral-50 transition-colors"
              >
                Stream
              </a>
            </nav>

            {/* Right side: Alerts & User */}
            <div className="flex items-center gap-4">
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

      <div className="max-w-4xl mx-auto p-6">

        {/* Error Message */}
        {error && (
          <div className="bg-accent-terra/10 border-2 border-accent-terra p-4 mb-6">
            <p className="body-default text-accent-terra font-medium">{error}</p>
          </div>
        )}

        {/* Selected Patient Card */}
        {selectedPatient ? (
          <div className="bg-white border border-neutral-200 p-6 mb-6 hover-lift rounded-lg">
            <div className="flex items-center gap-6">
              <img
                src={selectedPatient.photo_url}
                alt={selectedPatient.name}
                className="w-20 h-20 object-cover rounded-lg"
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
          <div className="bg-white border border-neutral-200 p-12 mb-6 text-center rounded-lg">
            <div className="mb-6">
              <div className="w-24 h-24 mx-auto bg-neutral-100 border border-neutral-200 flex items-center justify-center rounded-lg">
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
        <div className="bg-white border border-neutral-200 p-6 mb-6 rounded-lg">
          <div className="relative aspect-video bg-neutral-950 overflow-hidden mb-6 border border-neutral-200 rounded-lg">
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

            {/* Wake Word Listening Indicator */}
            {isListeningForWakeWord && !havenActive && (
              <div className="absolute bottom-4 left-4 px-4 py-2 bg-neutral-950/90 border border-primary-700">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse" />
                  <span className="label-uppercase text-primary-400 text-xs">
                    Listening for "Hey Haven"
                  </span>
                </div>
              </div>
            )}

            {/* Haven Voice Agent Conversation Overlay */}
            {havenActive && havenRoomData && (
              <div className="absolute inset-0">
                {/* Background Layer: AI Voice Animation */}
                <div className="absolute inset-0 z-0">
                  <AIVoiceAnimation isActive={voiceAssistantActive} />
                </div>

                {/* LiveKit Room Layer */}
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-8">
                  <LiveKitRoom
                    token={havenRoomData.token}
                    serverUrl={havenRoomData.url}
                    connect={true}
                    audio={true}
                    video={false}
                    className="w-full h-full flex items-center justify-center"
                  >
                    <div className="max-w-md w-full bg-white/70 backdrop-blur-md border border-neutral-300 p-8 rounded-lg shadow-xl">
                      {/* Header */}
                      <div className="flex items-center justify-center gap-3 mb-6">
                        <div className="w-4 h-4 bg-neutral-800 rounded-full animate-pulse" />
                        <h3 className="heading-section text-neutral-900">Haven AI Active</h3>
                      </div>

                      {/* Voice Assistant Audio and Visualizer */}
                      <HavenVoiceAssistant />

                      {/* Transcript Display */}
                      <div className="mb-6">
                        <div className="bg-neutral-100/80 border border-neutral-300 p-4 rounded-lg min-h-[100px]">
                          <p className="body-default text-neutral-800">
                            {havenTranscript || 'Listening...'}
                          </p>
                        </div>
                      </div>

                      {/* Instructions and Controls */}
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center gap-2 text-neutral-600 text-xs">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                          </svg>
                          <span className="label-uppercase">Speak naturally about your concern</span>
                        </div>

                        <button
                          onClick={endHavenSession}
                          className="px-4 py-2 bg-neutral-900 hover:bg-neutral-700 border border-neutral-900 text-white label-uppercase text-xs transition-colors rounded"
                        >
                          End Conversation
                        </button>
                      </div>
                    </div>
                  </LiveKitRoom>
                </div>
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
        <div className="bg-white border border-neutral-200 p-8 rounded-lg">
          <h2 className="heading-section text-neutral-950 mb-6 border-b border-neutral-200 pb-3">How to Use</h2>
          <ol className="space-y-4 body-default text-neutral-950">
            <li className="flex items-baseline gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">01</span>
              <span>Click &quot;Start Streaming&quot; button above</span>
            </li>
            <li className="flex items-baseline gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">02</span>
              <span>Allow camera permissions when prompted</span>
            </li>
            <li className="flex items-baseline gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">03</span>
              <span>On another computer, open the dashboard</span>
            </li>
            <li className="flex items-baseline gap-4">
              <span className="label-uppercase text-neutral-700 flex-shrink-0">04</span>
              <span>Look for your patient in the live feed section</span>
            </li>
            <li className="flex items-baseline gap-4">
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
          setShowModeSelector(true);
        }}
        activeStreams={activeStreams}
      />

      {/* Analysis Mode Selector Modal (Step 2) */}
      {showModeSelector && tempPatient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-neutral-950/80"
            onClick={() => setShowModeSelector(false)}
          />

          {/* Modal */}
          <div className="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto rounded-lg">
            <AnalysisModeSelector
              patient={tempPatient}
              onConfirm={(mode) => {
                setSelectedPatient(tempPatient);
                setAnalysisMode(mode);
                setShowModeSelector(false);

                // Save analysis mode to localStorage for dashboard to read
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
    </div>
  );
}
