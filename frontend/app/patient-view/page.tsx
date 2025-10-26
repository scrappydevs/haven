'use client';

import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react';
import { motion } from 'framer-motion';
import { LiveKitRoom, useVoiceAssistant, BarVisualizer, RoomAudioRenderer } from '@livekit/components-react';
import '@livekit/components-styles';
import PatientSearchModal from '@/components/PatientSearchModal';
import AnalysisModeSelector, { AnalysisMode } from '@/components/AnalysisModeSelector';
import AIVoiceAnimation from '@/components/AIVoiceAnimation';
import { getApiUrl, getWsUrl } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Patient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

// Extract HavenVoiceAssistant outside to prevent recreation on hot reload
function HavenVoiceAssistant({ 
  onTranscriptUpdate, 
  onError, 
  onDisconnect 
}: { 
  onTranscriptUpdate: (transcript: string) => void;
  onError: (error: string) => void;
  onDisconnect: () => void;
}) {
  const { state, audioTrack } = useVoiceAssistant();
  const lastStateRef = useRef<string>('');
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hasConnectedRef = useRef<boolean>(false);

  useEffect(() => {
    // Set a timeout to detect if the agent never connects
    // Only timeout if we never reach 'listening' state
    connectionTimeoutRef.current = setTimeout(() => {
      if (!hasConnectedRef.current && state !== 'listening' && state !== 'thinking' && state !== 'speaking') {
        console.error('❌ Haven voice agent connection timeout - backend agent worker not responding');
        console.error('   Current state:', state);
        console.error('   Start the backend agent: cd backend && ./start_haven_agent.sh');
        onError('Haven voice agent backend is not running. Start it with: cd backend && ./start_haven_agent.sh');
        onDisconnect();
      }
    }, 20000); // 20 second timeout (longer to account for cold starts)

    return () => {
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
      }
    };
  }, []); // Empty deps - only run once on mount

  useEffect(() => {
    if (state !== lastStateRef.current) {
      console.log(`🔊 Haven voice agent state changed: ${lastStateRef.current} → ${state}`);
      lastStateRef.current = state;

      // Mark as connected once we reach a successful state
      if (state === 'listening' || state === 'thinking' || state === 'speaking') {
        hasConnectedRef.current = true;
        // Clear timeout once we successfully connect
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
          console.log('✅ Haven voice agent connected successfully');
        }
      }

      const timer = setTimeout(() => {
        if (state === 'connecting') {
          onTranscriptUpdate('Waiting for Haven AI agent to join the room...');
        } else if (state === 'listening') {
          onTranscriptUpdate('🎤 Haven AI is listening. Speak naturally.');
        } else if (state === 'thinking') {
          onTranscriptUpdate('🤔 Haven AI is processing your response...');
        } else if (state === 'speaking') {
          onTranscriptUpdate('🗣️ Haven AI is speaking...');
        } else if (state === 'disconnected' && hasConnectedRef.current) {
          // Only show disconnect error if we were previously connected
          console.error('❌ Haven voice agent disconnected unexpectedly');
          onError('Haven voice agent disconnected. Check backend logs.');
          onDisconnect();
        }
      }, 120);

      return () => clearTimeout(timer);
    }
  }, [state, onTranscriptUpdate, onError, onDisconnect]);

  return (
    <>
      <RoomAudioRenderer />
      {audioTrack && (
        <div className="flex justify-center">
          <BarVisualizer state={state} barCount={6} trackRef={audioTrack} className="w-full" />
        </div>
      )}
    </>
  );
}

export default function PatientViewPage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const captureCleanupRef = useRef<(() => void) | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const isConnectingRef = useRef<boolean>(false);
  const selectedPatientRef = useRef<Patient | null>(null);
  const viewStartedRef = useRef<boolean>(false);
  const havenActiveRef = useRef<boolean>(false);
  const suppressDashboardRedirectRef = useRef<boolean>(false);

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [tempPatient, setTempPatient] = useState<Patient | null>(null);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('enhanced');
  const [modeSelectionInitial, setModeSelectionInitial] = useState<AnalysisMode>('enhanced');
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

  const [havenActive, setHavenActive] = useState(false);
  const [havenTranscript, setHavenTranscript] = useState('');
  const [havenRoomData, setHavenRoomData] = useState<{
    token: string;
    url: string;
    room_name: string;
    session_id: string;
  } | null>(null);
  const [isListeningForSpeech, setIsListeningForSpeech] = useState(false);
  const [listenerHeartbeat, setListenerHeartbeat] = useState(0);
  const [voiceAgentUnavailable, setVoiceAgentUnavailable] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const listenerRestartRef = useRef<NodeJS.Timeout | null>(null);
  const listenerStartingRef = useRef<boolean>(false);
  const listenerTriggeredRef = useRef<boolean>(false);
  const havenStartingRef = useRef<boolean>(false);
  const listenerInitializedRef = useRef<boolean>(false);

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

  useEffect(() => {
    setIsMicActive(havenActive || isListeningForSpeech);
  }, [havenActive, isListeningForSpeech]);

  useEffect(() => {
    selectedPatientRef.current = selectedPatient;
  }, [selectedPatient]);

  useEffect(() => {
    viewStartedRef.current = viewStarted;
  }, [viewStarted]);

  useEffect(() => {
    havenActiveRef.current = havenActive;
  }, [havenActive]);

  // Ensure video element has stream when it becomes visible
  useEffect(() => {
    if (!showAIAnimation && videoRef.current && streamRef.current && isStreaming) {
      if (videoRef.current.srcObject !== streamRef.current) {
        console.log('🔄 Reconnecting video element to stream');
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play().catch(err => {
          console.warn('Video play error after reconnect:', err);
        });
      }
    }
  }, [showAIAnimation, isStreaming]);

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

  const stopListenerAgent = useCallback(() => {
    if (listenerRestartRef.current) {
      clearTimeout(listenerRestartRef.current);
      listenerRestartRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      } catch (err) {
        console.warn('Error stopping listener agent:', err);
      }
    }

    recognitionRef.current = null;
    listenerStartingRef.current = false;
    listenerTriggeredRef.current = false;
    listenerInitializedRef.current = false;
    setIsListeningForSpeech(false);
  }, []);

  const startHavenSession = useCallback(
    async (source: 'manual' | 'listener', triggerTranscript?: string) => {
      const patient = selectedPatientRef.current;
      if (!patient) {
        setError('Please select a patient first');
        return;
      }

      if (!viewStartedRef.current) {
        console.warn('⚠️ Voice agent requires the patient view to be active');
        return;
      }

      if (havenStartingRef.current || havenActiveRef.current) {
        console.log('⚠️ Haven session already active or starting');
        return;
      }

      console.log(`🛡️ Starting Haven session via ${source} trigger`, {
        patient: patient.patient_id,
        transcript: triggerTranscript
      });

      havenStartingRef.current = true;
      havenActiveRef.current = true;
      listenerTriggeredRef.current = source === 'listener';

      setError(null);
      setVoiceAgentUnavailable(null);
      setShowAIAnimation(true);
      setHavenActive(true);
      setHavenTranscript(
        source === 'listener'
          ? 'I heard you. Connecting you with Haven AI...'
          : 'Connecting to Haven AI...'
      );

      stopListenerAgent();

      try {
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/api/haven/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: patient.patient_id })
        });

        let data: any = null;
        let parseError: Error | null = null;
        try {
          data = await response.json();
        } catch (err) {
          parseError = err as Error;
        }

        if (!response.ok) {
          const detail =
            data?.error ||
            data?.detail ||
            parseError?.message ||
            `Voice agent start failed (${response.status})`;
          throw new Error(detail);
        }

        if (!data?.token || !data?.room_name || !data?.url) {
          console.error('Voice agent start response missing required fields:', data);
          throw new Error(
            `Voice agent response missing session data${data ? ` (${JSON.stringify(data)})` : ''}.`
          );
        }

        setHavenRoomData({
          token: data.token,
          url: data.url,
          room_name: data.room_name,
          session_id: data.session_id
        });

        console.log('✅ Haven session ready:', data.room_name);
        console.log('🔊 Connecting to LiveKit room:', data.url);
        console.log('🔊 Waiting for Haven voice agent to join room...');
        console.log('💡 If stuck, ensure backend agent is running: cd backend && ./start_haven_agent.sh');
        setHavenTranscript('Connecting to room. Waiting for Haven AI backend agent to join...');
      } catch (err: any) {
        console.error('❌ Failed to start Haven session:', err);
        const errorMessage = err?.message ?? 'unknown error';
        setError('Failed to start voice assistant: ' + errorMessage);
        setHavenActive(false);
        setShowAIAnimation(false);
        setHavenRoomData(null);
        listenerTriggeredRef.current = false;
        havenActiveRef.current = false;
        if (errorMessage.toLowerCase().includes('livekit configuration incomplete') ||
            errorMessage.toLowerCase().includes('livekit sdk not installed')) {
          setVoiceAgentUnavailable('Backend missing LiveKit dependencies. Install livekit packages and restart server.');
          stopListenerAgent();
        } else if (source === 'listener' && viewStartedRef.current && selectedPatientRef.current) {
          setListenerHeartbeat((prev) => prev + 1);
        }
      } finally {
        havenStartingRef.current = false;
      }
    },
    [setError, stopListenerAgent, setVoiceAgentUnavailable]
  );

  const startListenerAgent = useCallback(async () => {
    const patient = selectedPatientRef.current;
    if (!patient || !viewStartedRef.current || havenActiveRef.current) {
      return;
    }

    if (voiceAgentUnavailable) {
      return;
    }

    if (listenerStartingRef.current || recognitionRef.current) {
      console.log('⏭️ Listener already starting or running, skipping...');
      return;
    }

    if (listenerInitializedRef.current) {
      console.log('⏭️ Listener already initialized, skipping restart...');
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    // Request microphone permissions first
    if (typeof navigator.mediaDevices !== 'undefined' && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Stop the stream immediately - we just wanted to get permissions
        stream.getTracks().forEach(track => track.stop());
        console.log('✅ Microphone permission granted for listener');
      } catch (err) {
        console.error('❌ Microphone permission denied:', err);
        setError('Microphone permission denied. Please allow microphone access.');
        setVoiceAgentUnavailable('Microphone access required');
        return;
      }
    }

    listenerStartingRef.current = true;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false; // Changed to false to reduce noise
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('🎧 Listener agent started');
      listenerStartingRef.current = false;
      listenerInitializedRef.current = true;
      setIsListeningForSpeech(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join(' ')
        .trim();

      const isFinal = event.results[event.results.length - 1].isFinal;

      if (!listenerTriggeredRef.current && isFinal && transcript.length >= 3) {
        console.log('🔈 Listener detected speech:', transcript);
        listenerTriggeredRef.current = true;
        try {
          recognition.stop();
        } catch (stopErr) {
          console.warn('Listener stop error:', stopErr);
        }
        void startHavenSession('listener', transcript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('❌ Listener agent error:', event.error);
      listenerStartingRef.current = false;
      setIsListeningForSpeech(false);

      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow microphone access for speech detection.');
        setVoiceAgentUnavailable('Microphone access denied');
        stopListenerAgent();
      } else if (event.error === 'audio-capture') {
        console.warn('⚠️ Microphone busy or unavailable. Will retry...');
        // Don't restart immediately for audio-capture, wait longer
        if (!havenActiveRef.current && viewStartedRef.current) {
          setTimeout(() => {
            setListenerHeartbeat((prev) => prev + 1);
          }, 2000); // Wait 2 seconds before retry
        }
      } else if (event.error === 'no-speech') {
        // This is normal - just means no speech detected, restart listener
        console.log('🔇 No speech detected, restarting listener...');
        setListenerHeartbeat((prev) => prev + 1);
      } else if (event.error !== 'aborted') {
        console.warn('⚠️ Speech recognition error, will retry:', event.error);
        setListenerHeartbeat((prev) => prev + 1);
      }
    };

    recognition.onend = () => {
      console.log('🛑 Listener agent ended');
      recognitionRef.current = null;
      setIsListeningForSpeech(false);

      if (!havenActiveRef.current && viewStartedRef.current && selectedPatientRef.current) {
        setListenerHeartbeat((prev) => prev + 1);
      }
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
    } catch (err) {
      console.error('❌ Failed to start listener agent:', err);
      listenerStartingRef.current = false;
      setError('Failed to start microphone for speech detection');
    }
  }, [setError, startHavenSession, voiceAgentUnavailable, setVoiceAgentUnavailable, stopListenerAgent]);

  const endHavenSession = useCallback(async () => {
    if (!havenActiveRef.current) {
      return;
    }

    const patient = selectedPatientRef.current;

    console.log('🛡️ Ending Haven voice session');

    if (havenRoomData && patient) {
      try {
        const apiUrl = getApiUrl();
        const summaryPayload = {
          patient_id: patient.patient_id,
          session_id: havenRoomData.session_id,
          conversation_summary: {
            full_transcript_text: havenTranscript,
            extracted_info: {
              symptom_description: 'Patient reported concern',
              body_location: null,
              pain_level: null,
              duration: null
            }
          }
        };

        const response = await fetch(`${apiUrl}/api/haven/conversation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(summaryPayload)
        });

        const result = await response.json();
        if (!result.success) {
          console.warn('⚠️ Failed to save Haven conversation:', result.error);
        }
      } catch (err) {
        console.error('❌ Error saving Haven conversation:', err);
      }
    }

    stopListenerAgent();
    setHavenActive(false);
    setHavenTranscript('');
    setHavenRoomData(null);
    setShowAIAnimation(false);
    listenerTriggeredRef.current = false;
    havenActiveRef.current = false;
  }, [havenRoomData, havenTranscript, stopListenerAgent]);

  useEffect(() => {
    if (listenerRestartRef.current) {
      clearTimeout(listenerRestartRef.current);
      listenerRestartRef.current = null;
    }

    // Skip if already initialized and no heartbeat change (prevents hot reload restarts)
    if (listenerInitializedRef.current && recognitionRef.current && listenerHeartbeat === 0) {
      console.log('⏭️ Listener already running, skipping restart (hot reload protection)');
      return;
    }

    if (viewStarted && selectedPatient && !havenActive && !voiceAgentUnavailable) {
      // Longer delay to prevent restart loops
      listenerRestartRef.current = setTimeout(() => {
        startListenerAgent();
      }, 1000); // Increased from 300ms to 1 second
    } else if (!viewStarted || !selectedPatient) {
      stopListenerAgent();
    }

    return () => {
      if (listenerRestartRef.current) {
        clearTimeout(listenerRestartRef.current);
        listenerRestartRef.current = null;
      }
      // Don't stop on cleanup if we're just hot reloading and listener is active
      if (!listenerInitializedRef.current || !recognitionRef.current) {
        stopListenerAgent();
      }
    };
  }, [viewStarted, selectedPatient, havenActive, listenerHeartbeat, voiceAgentUnavailable, startListenerAgent, stopListenerAgent]);

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

    if (havenActiveRef.current) {
      void endHavenSession();
    } else {
      stopListenerAgent();
      setHavenTranscript('');
      setShowAIAnimation(false);
      setHavenRoomData(null);
      havenActiveRef.current = false;
    }

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
  };

  // Start streaming when view becomes active (after video element is rendered)
  useEffect(() => {
    if (viewStarted && selectedPatient && !isStreaming && !isConnecting) {
      startStreaming();
    }
  }, [viewStarted, selectedPatient, isStreaming, isConnecting]);

  const handleVoiceAgentCardClick = () => {
    if (!selectedPatient) {
      setError('Select a patient before activating the voice agent.');
      return;
    }

    if (!viewStartedRef.current) {
      setError('Start the patient view before activating the voice agent.');
      return;
    }

    if (voiceAgentUnavailable) {
      setError(voiceAgentUnavailable);
      return;
    }

    if (havenStartingRef.current) {
      console.log('Haven voice agent is connecting. Please wait...');
      return;
    }

    // Start Haven session if not already active
    if (!havenActiveRef.current && !havenStartingRef.current) {
      void startHavenSession('manual');
    }
  };

  const handleMicButtonClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();

    if (!selectedPatient) {
      setError('Select a patient before activating the voice agent.');
      return;
    }

    if (!viewStartedRef.current) {
      setError('Start the patient view before activating the voice agent.');
      return;
    }

    if (voiceAgentUnavailable) {
      setError(voiceAgentUnavailable);
      return;
    }

    if (havenStartingRef.current) {
      console.log('⚠️ Haven voice agent is connecting. Please wait...');
      return;
    }

    setShowAIAnimation(true);

    if (havenActiveRef.current) {
      void endHavenSession();
    } else if (!havenStartingRef.current) {
      void startHavenSession('manual');
    }
  };

  // Callbacks for HavenVoiceAssistant
  const handleTranscriptUpdate = useCallback((transcript: string) => {
    setHavenTranscript(transcript);
  }, []);

  const handleVoiceError = useCallback((error: string) => {
    setError(error);
  }, []);

  const handleVoiceDisconnect = useCallback(() => {
    setHavenActive(false);
    setShowAIAnimation(false);
    setHavenRoomData(null);
    havenActiveRef.current = false;
  }, []);

  const handlePatientModalClose = useCallback(() => {
    setShowPatientModal(false);
    if (suppressDashboardRedirectRef.current) {
      suppressDashboardRedirectRef.current = false;
      return;
    }
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Patient selection flow */}
      <PatientSearchModal
        isOpen={showPatientModal && !selectedPatient}
        onClose={handlePatientModalClose}
        onSelect={(patient) => {
          suppressDashboardRedirectRef.current = true;
          const savedMode = typeof window !== 'undefined'
            ? localStorage.getItem(`analysis-mode-${patient.patient_id}`)
            : null;
          const initialMode = savedMode === 'normal' || savedMode === 'enhanced' ? savedMode : 'enhanced';

          setModeSelectionInitial(initialMode);
          setTempPatient(patient);
          setShowPatientModal(false);
          setShowModeSelector(true);
        }}
        activeStreams={activeStreams}
      />

      {/* Analysis mode selector modal */}
      {showModeSelector && tempPatient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-neutral-950/40"
            onClick={() => {
              setShowModeSelector(false);
              setTempPatient(null);

              if (!selectedPatient) {
                setShowPatientModal(true);
              }
            }}
          />
          <div className="relative max-w-2xl w-full max-h-[80vh] overflow-y-auto rounded-lg">
            <AnalysisModeSelector
              patient={tempPatient}
              initialMode={modeSelectionInitial}
              onConfirm={(mode) => {
                const patientToSelect = tempPatient;
                if (!patientToSelect) {
                  setShowModeSelector(false);
                  return;
                }

                setSelectedPatient(patientToSelect);
                setAnalysisMode(mode);
                setModeSelectionInitial(mode);
                setShowModeSelector(false);

                localStorage.setItem(
                  `analysis-mode-${patientToSelect.patient_id}`,
                  mode
                );
                console.log(`💾 Saved analysis mode for ${patientToSelect.patient_id}:`, mode);

                console.log(`✅ Selected patient ${patientToSelect.patient_id} with mode:`, mode);
                setTempPatient(null);
              }}
              onBack={() => {
                setShowModeSelector(false);
                setTempPatient(null);

                if (!selectedPatient) {
                  setShowPatientModal(true);
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Once patient is selected, show the view */}
      {selectedPatient && !viewStarted && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-neutral-950/40">
          <div className="bg-white border border-neutral-200 max-w-2xl w-full p-8 rounded-lg">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-playfair font-black text-primary-950 mb-2">Patient View</h2>
              <p className="text-neutral-600">Ready to start monitoring</p>
            </div>

              <div className="flex justify-start mb-6">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 text-xs text-neutral-600 hover:text-primary-700 transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={1.5}
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15.75 19.5L8.25 12l7.5-7.5"
                    />
                  </svg>
                  <span className="label-uppercase tracking-widest">Back to Dashboard</span>
                </Link>
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
                onClick={() => {
                  if (!selectedPatient) {
                    return;
                  }

                  setModeSelectionInitial(analysisMode);
                  setTempPatient(selectedPatient);
                  setShowPatientModal(false);
                  setShowModeSelector(true);
                }}
                className="flex-1 px-6 py-4 border-2 border-neutral-300 text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 label-uppercase transition-colors"
              >
                Change Mode
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
          <div className="flex-1 py-6">
            <div className="container mx-auto flex flex-col gap-6 px-6" style={{ height: 'calc(100vh - 200px)' }}>
              {/* Video/Animation Container */}
              <div className="flex-1 relative rounded-lg overflow-hidden bg-neutral-950">
                {/* Video Display */}
                {!showAIAnimation && (
                  <>
                <video
                  ref={videoRef}
                  className="absolute inset-0 w-full h-full object-cover"
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
                </>
                )}

                {/* AI Animation View (when Haven is not active but animation is toggled) */}
                {showAIAnimation && !havenActive && (
                  <div className="absolute inset-0">
                    <AIVoiceAnimation isActive={isMicActive} />
                  </div>
                )}

                {/* Haven Voice Agent Conversation Overlay with AI Animation Background */}
                {havenActive && havenRoomData && (
                  <div className="absolute inset-0">
                    {/* Background Layer: AI Voice Animation - Right Side */}
                    <div className="absolute inset-0 z-0">
                      <AIVoiceAnimation isActive={isMicActive} />
                    </div>

                    {/* LiveKit Room Layer - Left Side Panel */}
                    <div className="absolute inset-0 z-10 flex items-center justify-start p-8">
                      <LiveKitRoom
                        key={havenRoomData.session_id}
                        token={havenRoomData.token}
                        serverUrl={havenRoomData.url}
                        connect={true}
                        audio={true}
                        video={false}
                        className="h-full flex items-center"
                        options={{
                          // Prevent reconnection loops during hot reload
                          disconnectOnPageLeave: false,
                        }}
                      >
                        <div className="max-w-md w-full bg-white/70 backdrop-blur-md border border-neutral-300 p-8 rounded-lg shadow-xl">
                          {/* Header */}
                          <div className="flex items-center justify-center gap-3 mb-6">
                            <div className="w-4 h-4 bg-neutral-800 rounded-full animate-pulse" />
                            <h3 className="heading-section text-neutral-900">Haven AI Active</h3>
                          </div>

                          {/* Voice Assistant Audio and Visualizer */}
                          <HavenVoiceAssistant 
                            onTranscriptUpdate={handleTranscriptUpdate}
                            onError={handleVoiceError}
                            onDisconnect={handleVoiceDisconnect}
                          />

                          {/* Transcript Display */}
                          <div className="mb-6">
                            <div className="bg-neutral-100/80 border border-neutral-300 p-4 rounded-lg min-h-[100px]">
                              <p className="body-default text-neutral-800">
                                {havenTranscript || 'Listening...'}
                              </p>
                              {(havenTranscript.includes('Waiting') || havenTranscript.includes('Connecting to room')) && (
                                <div className="mt-3 pt-3 border-t border-neutral-200">
                                  <p className="text-xs font-medium text-neutral-600 mb-1">Backend Required:</p>
                                  <code className="block bg-neutral-200 text-neutral-900 px-2 py-1.5 rounded text-xs font-mono">
                                    cd backend && ./start_haven_agent.sh
                                  </code>
                                  <p className="text-xs text-neutral-500 mt-2">
                                    The Haven voice agent worker must be running to handle the conversation.
                                  </p>
                                </div>
                              )}
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

              {/* Bottom AI Voice Agent Card */}
              <div>
              <motion.div
                onClick={handleVoiceAgentCardClick}
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
                        {havenActive
                          ? 'Voice conversation in progress'
                          : voiceAgentUnavailable
                            ? 'Voice agent unavailable. Check backend configuration.'
                            : isListeningForSpeech
                              ? 'Listening for patient speech...'
                              : 'Click to start Haven voice agent'}
                      </p>
                    </div>
                  </div>

                  {/* Center: Status Indicator */}
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      havenActive
                        ? 'bg-accent-terra animate-pulse'
                        : voiceAgentUnavailable
                          ? 'bg-accent-terra/70'
                          : isListeningForSpeech
                            ? 'bg-primary-500 animate-pulse'
                            : 'bg-neutral-400'
                    }`} />
                    <span className="text-xs text-neutral-600">
                      {havenActive
                        ? 'Active'
                        : voiceAgentUnavailable
                          ? 'Unavailable'
                          : isListeningForSpeech
                            ? 'Listening'
                            : 'Ready'}
                    </span>
                  </div>

                  {/* Right: Microphone Button */}
                  <button
                    onClick={handleMicButtonClick}
                    className={`w-12 h-12 rounded-full transition-all duration-200 flex items-center justify-center ${
                      havenActive
                        ? 'bg-accent-terra hover:bg-accent-terra/90 shadow-lg'
                        : voiceAgentUnavailable
                          ? 'bg-neutral-300 cursor-not-allowed'
                          : isListeningForSpeech
                            ? 'bg-primary-200 hover:bg-primary-300'
                            : 'bg-neutral-200 hover:bg-neutral-300'
                    }`}
                  >
                    {havenActive ? (
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
          </div>

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}
    </div>
  );
}
