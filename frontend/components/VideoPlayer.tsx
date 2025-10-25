'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { getApiUrl, getWsUrl } from '@/lib/api';

interface VideoPlayerProps {
  patient: {
    id: number;
    name: string;
    age?: number;
    condition?: string;
    baseline_vitals?: {
      heart_rate: number;
    };
  };
  isLive?: boolean;
  isSelected?: boolean;
  onCvDataUpdate?: (patientId: number, data: CVData) => void;
  onAgentMessage?: (patientId: number, message: any) => void;  // Agent state changes and alerts
  patientId?: string;  // Patient ID to filter WebSocket messages (e.g., "P-001")
  monitoringConditions?: string[];  // Monitoring conditions for this patient (e.g., ["CRS", "SEIZURE"])
  fullscreenMode?: boolean;  // Large view for detail mode
}

interface Landmark {
  id: number;
  x: number;  // Normalized 0-1
  y: number;  // Normalized 0-1
  type: string;
  color: string;
}

interface HeadPoseAxes {
  origin: { x: number; y: number };
  x_axis: { x: number; y: number; color: string };
  y_axis: { x: number; y: number; color: string };
  z_axis: { x: number; y: number; color: string };
}

interface CVData {
  frame?: string;
  landmarks?: Landmark[];
  head_pose_axes?: HeadPoseAxes | null;
  metrics?: {
    crs_score: number;
    heart_rate: number;
    respiratory_rate: number;
    alert: boolean;
    head_pitch?: number;
    head_yaw?: number;
    head_roll?: number;
    eye_openness?: number;
    attention_score?: number;
  };
  // Legacy flat format for backward compatibility with pre-recorded videos
  crs_score?: number;
  heart_rate?: number;
  respiratory_rate?: number;
  alert?: boolean;
  head_pitch?: number;
  head_yaw?: number;
  head_roll?: number;
  eye_openness?: number;
  attention_score?: number;
}

export default function VideoPlayer({ patient, isLive = false, isSelected = false, onCvDataUpdate, onAgentMessage, patientId, fullscreenMode = false }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [cvData, setCvData] = useState<CVData>({
    landmarks: [],
    head_pose_axes: null,
    metrics: {  // Initialize with dummy metrics to prevent loading overlay
      heart_rate: 0,
      respiratory_rate: 0,
      crs_score: 0,
      alert: false
    }
  });
  const [alertFired, setAlertFired] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const [latestOverlayData, setLatestOverlayData] = useState<any>(null);

  // CV data callback effect - notify parent when data changes and player is selected
  useEffect(() => {
    if (isSelected && cvData && onCvDataUpdate) {
      onCvDataUpdate(patient.id, cvData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cvData, isSelected]); // Intentionally excluding onCvDataUpdate and patient.id to avoid infinite loops

  // Persistent canvas overlay rendering - redraws overlays at 60 FPS using cached data
  useEffect(() => {
    if (!isLive || !latestOverlayData) return;

    const canvas = overlayCanvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;

    let animationId: number;

    const drawOverlays = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Match canvas size to image display size
      const rect = img.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;

      // Clear previous frame
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw landmark connections
      if (latestOverlayData.connections && latestOverlayData.landmarks) {
        const landmarkMap = new Map();
        latestOverlayData.landmarks.forEach((lm: any) => {
          landmarkMap.set(lm.id, {
            x: lm.x * canvas.width,
            y: lm.y * canvas.height,
            color: lm.color
          });
        });

        ctx.strokeStyle = '#00FF00';  // Green lines
        ctx.lineWidth = 1;

        latestOverlayData.connections.forEach(([startId, endId]: [number, number]) => {
          const start = landmarkMap.get(startId);
          const end = landmarkMap.get(endId);
          if (start && end) {
            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.stroke();
          }
        });

        // Draw landmark points with colors
        latestOverlayData.landmarks.forEach((lm: any) => {
          const colorMap: Record<string, string> = {
            'green': '#00FF00',
            'cyan': '#00FFFF',
            'red': '#FF0000'
          };
          ctx.fillStyle = colorMap[lm.color] || '#00FF00';
          ctx.beginPath();
          ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 3, 0, 2 * Math.PI);
          ctx.fill();
        });
      }

      // Draw head pose axes
      if (latestOverlayData.head_pose_axes) {
        const axes = latestOverlayData.head_pose_axes;
        const origin = axes.origin;

        const colorMap: Record<string, string> = {
          'red': '#FF0000',
          'green': '#00FF00',
          'blue': '#0000FF'
        };

        // Scale coordinates to canvas size
        const scaleX = canvas.width / (img.naturalWidth || canvas.width);
        const scaleY = canvas.height / (img.naturalHeight || canvas.height);

        ctx.lineWidth = 2;

        // Draw X axis (Red)
        ctx.strokeStyle = colorMap[axes.x_axis.color];
        ctx.beginPath();
        ctx.moveTo(origin.x * scaleX, origin.y * scaleY);
        ctx.lineTo(axes.x_axis.x * scaleX, axes.x_axis.y * scaleY);
        ctx.stroke();

        // Draw Y axis (Green)
        ctx.strokeStyle = colorMap[axes.y_axis.color];
        ctx.beginPath();
        ctx.moveTo(origin.x * scaleX, origin.y * scaleY);
        ctx.lineTo(axes.y_axis.x * scaleX, axes.y_axis.y * scaleY);
        ctx.stroke();

        // Draw Z axis (Blue)
        ctx.strokeStyle = colorMap[axes.z_axis.color];
        ctx.beginPath();
        ctx.moveTo(origin.x * scaleX, origin.y * scaleY);
        ctx.lineTo(axes.z_axis.x * scaleX, axes.z_axis.y * scaleY);
        ctx.stroke();
      }

      // Request next frame
      animationId = requestAnimationFrame(drawOverlays);
    };

    // Start animation loop
    animationId = requestAnimationFrame(drawOverlays);

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [latestOverlayData, isLive]);

  // WebSocket effect for live feed only - separate from pre-recorded
  useEffect(() => {
    if (!isLive) return;

    const wsUrl = `${getWsUrl()}/ws/view`;
    console.log('🔌 Viewer connecting to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Connected to live stream viewer');
    };

    ws.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error('❌ JSON parse error:', e);
        console.error('📦 Raw data (first 200 chars):', typeof event.data === 'string' ? event.data.substring(0, 200) : event.data);
        return; // Skip this message
      }

      // Filter by patient_id if provided, otherwise accept all messages
      if (!patientId || data.patient_id === patientId) {
        // Handle raw frame update (30 FPS smooth video)
        if (data.type === 'live_frame' && data.data?.frame) {
          if (imgRef.current) {
            imgRef.current.src = data.data.frame;
          }
        }

        // Handle overlay data (15 FPS updates, persists via requestAnimationFrame)
        if (data.type === 'overlay_data' && data.data) {
          // Update overlay data (will be redrawn at 60 FPS by animation loop)
          setLatestOverlayData(data.data);

          // Update metrics
          if (data.data.metrics) {
            setCvData({
              frame: undefined,
              landmarks: data.data.landmarks || [],
              head_pose_axes: data.data.head_pose_axes,
              metrics: data.data.metrics,
              // Legacy flat format support
              crs_score: data.data.metrics?.crs_score,
              heart_rate: data.data.metrics?.heart_rate,
              respiratory_rate: data.data.metrics?.respiratory_rate,
              alert: data.data.metrics?.alert,
              head_pitch: data.data.metrics?.head_pitch,
              head_yaw: data.data.metrics?.head_yaw,
              head_roll: data.data.metrics?.head_roll,
              eye_openness: data.data.metrics?.eye_openness,
              attention_score: data.data.metrics?.attention_score
            });

            // Check for alerts
            if (data.data.metrics?.alert && !alertFired) {
              setAlertFired(true);
              console.log(`🚨 ALERT FIRED for ${data.patient_id}! CRS:`, data.data.metrics.crs_score);
              const audio = new Audio('/alert.mp3');
              audio.play().catch(e => console.log('Audio play failed:', e));
            }
          }
        }

        // Handle agent thinking (analyzing)
        if (data.type === 'agent_thinking') {
          console.log(`🤖 Agent thinking for ${data.patient_id}:`, data.message);
          if (onAgentMessage) {
            onAgentMessage(patient.id, data);
          }
        }

        // Handle agent reasoning (Claude's analysis)
        if (data.type === 'agent_reasoning') {
          console.log(`🤖 Agent reasoning for ${data.patient_id}:`, data.reasoning);
          if (onAgentMessage) {
            onAgentMessage(patient.id, data);
          }
        }

        // Handle monitoring state changes from agent
        if (data.type === 'monitoring_state_change') {
          console.log(`🤖 Monitoring state change for ${data.patient_id}:`, data.level);
          if (onAgentMessage) {
            onAgentMessage(patient.id, data);
          }
        }

        // Handle agent alerts
        if (data.type === 'agent_alert') {
          console.log(`🤖 Agent alert for ${data.patient_id}:`, data.message);
          if (onAgentMessage) {
            onAgentMessage(patient.id, data);
          }
        }
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('❌ Disconnected from live stream');
    };

    return () => {
      console.log('🧹 Cleaning up WebSocket');
      ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLive]); // Intentionally excluding alertFired - don't reconnect WebSocket when alert fires

  // Pre-recorded video polling effect - separate from live
  useEffect(() => {
    if (isLive) return; // Skip if live feed

    const video = videoRef.current;
    if (!video) return;

    const interval = setInterval(() => {
      const time = video.currentTime;
      setCurrentTime(time);

      const apiUrl = getApiUrl();
      const timestamp = time.toFixed(1);
      fetch(`${apiUrl}/cv-data/${patient.id}/${timestamp}`)
        .then(res => res.json())
        .then(data => {
          // Normalize data structure to match live feed format
          setCvData({
            frame: data.frame,
            landmarks: data.landmarks || [],
            head_pose_axes: data.head_pose_axes || null,
            metrics: data.metrics,
            // Legacy flat format support
            crs_score: data.metrics?.crs_score || data.crs_score,
            heart_rate: data.metrics?.heart_rate || data.heart_rate,
            respiratory_rate: data.metrics?.respiratory_rate || data.respiratory_rate,
            alert: data.metrics?.alert || data.alert,
            head_pitch: data.metrics?.head_pitch || data.head_pitch,
            head_yaw: data.metrics?.head_yaw || data.head_yaw,
            head_roll: data.metrics?.head_roll || data.head_roll,
            eye_openness: data.metrics?.eye_openness || data.eye_openness,
            attention_score: data.metrics?.attention_score || data.attention_score
          });

          // Handle both nested (metrics.alert) and flat (alert) formats
          const isAlert = data.metrics?.alert || data.alert;
          if (isAlert && !alertFired) {
            setAlertFired(true);
            const audio = new Audio('/alert.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
          }
        })
        .catch(err => console.error('Error fetching CV data:', err));
    }, 1000);

    return () => clearInterval(interval);
  }, [patient.id, isLive, alertFired]);

  return (
    <motion.div
      className={`relative rounded-lg overflow-hidden border transition-all duration-200 ${
        fullscreenMode ? 'h-full' : ''
      } ${
        alertFired
          ? 'border-red-500 shadow-lg shadow-red-500/50'
          : isSelected
          ? 'border-blue-500 shadow-lg shadow-blue-500/30'
          : 'border-neutral-200'
      }`}
      animate={alertFired ? { scale: [1, 1.02, 1] } : {}}
      transition={{ repeat: alertFired ? Infinity : 0, duration: 1 }}
    >
      {/* Video Element - 30 FPS video + persistent canvas overlays */}
      {isLive ? (
        <div className={`relative w-full bg-neutral-950 ${fullscreenMode ? 'h-full' : 'aspect-video'}`}>
          <img
            ref={imgRef}
            className="w-full h-full object-cover"
            alt="Live stream"
            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
          />
          {/* Canvas overlay for persistent landmark and pose rendering */}
          <canvas
            ref={overlayCanvasRef}
            className="absolute inset-0 pointer-events-none"
          />
        </div>
      ) : patient.id <= 5 ? (
        <video
          ref={videoRef}
          src={`/videos/patient-${patient.id}.mp4`}
          autoPlay
          loop
          muted
          playsInline
          className={`w-full object-cover ${fullscreenMode ? 'h-full' : 'aspect-video'}`}
        />
      ) : (
        <div className={`w-full bg-neutral-100 border border-neutral-200 flex items-center justify-center text-neutral-400 ${fullscreenMode ? 'h-full' : 'aspect-video'}`}>
          <span className="text-sm">No video available</span>
        </div>
      )}

      {/* Alert Pulse Indicator (minimal corner badge) */}
      {alertFired && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-3 right-3 bg-accent-terra text-white px-3 py-1.5 text-sm font-medium rounded"
        >
          ALERT
        </motion.div>
      )}

      {/* Loading State - only show if no metrics data yet */}
      {!cvData?.metrics && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-950/50">
          <div className="text-center">
            <div className="text-white text-sm font-light mb-2">
              {isLive ? 'Waiting for live stream...' : 'Loading CV analysis...'}
            </div>
            {isLive && (
              <div className="text-neutral-300 text-xs font-light">
                Make sure streaming is active on /stream page
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}
