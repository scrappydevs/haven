'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

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

export default function VideoPlayer({ patient, isLive = false, isSelected = false, onCvDataUpdate, patientId, fullscreenMode = false }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [cvData, setCvData] = useState<CVData | null>(null);
  const [alertFired, setAlertFired] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // CV data callback effect - notify parent when data changes and player is selected
  useEffect(() => {
    if (isSelected && cvData && onCvDataUpdate) {
      onCvDataUpdate(patient.id, cvData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cvData, isSelected]); // Intentionally excluding onCvDataUpdate and patient.id to avoid infinite loops

  // Canvas overlay drawing effect - runs whenever CV data updates
  useEffect(() => {
    if (!cvData || !isLive) return;  // Only draw overlays for live feeds

    const canvas = overlayCanvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Match canvas size to image display size
    const rect = img.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear previous frame
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw landmarks and connections
    if (cvData.landmarks && cvData.landmarks.length > 0) {
      // Create a map for easy landmark lookup by type
      const landmarkMap = new Map();
      cvData.landmarks.forEach(lm => {
        landmarkMap.set(lm.type, {
          x: lm.x * canvas.width,
          y: lm.y * canvas.height
        });
      });

      // Define connections between landmarks - "super cool" tactical HUD style
      const connections = [
        // Face perimeter frame
        ['forehead', 'left_face'],
        ['left_face', 'chin'],
        ['chin', 'right_face'],
        ['right_face', 'forehead'],

        // Eye crosshairs
        ['left_eye_inner', 'nose_tip'],
        ['right_eye_inner', 'nose_tip'],
        ['left_eye_outer', 'left_face'],
        ['right_eye_outer', 'right_face'],

        // Center axis (nose to mouth)
        ['nose_tip', 'upper_lip'],
        ['upper_lip', 'lower_lip'],
        ['lower_lip', 'chin'],

        // Cheek scanlines (diagonal accents)
        ['left_cheek', 'nose_tip'],
        ['right_cheek', 'nose_tip'],
        ['left_cheek', 'upper_lip'],
        ['right_cheek', 'upper_lip'],
      ];

      // Draw connections (thin green lines)
      ctx.strokeStyle = '#00FF00';  // Green
      ctx.lineWidth = 1;
      connections.forEach(([start, end]) => {
        const startPoint = landmarkMap.get(start);
        const endPoint = landmarkMap.get(end);
        if (startPoint && endPoint) {
          ctx.beginPath();
          ctx.moveTo(startPoint.x, startPoint.y);
          ctx.lineTo(endPoint.x, endPoint.y);
          ctx.stroke();
        }
      });

      // Draw landmark points (green)
      ctx.fillStyle = '#00FF00';  // Green
      cvData.landmarks.forEach((lm) => {
        ctx.beginPath();
        ctx.arc(
          lm.x * canvas.width,
          lm.y * canvas.height,
          3,  // Radius
          0,
          2 * Math.PI
        );
        ctx.fill();
      });
    }

    // Draw head pose axes
    if (cvData.head_pose_axes) {
      const axes = cvData.head_pose_axes;
      const origin = axes.origin;

      // Scale axis coordinates to match image display size
      const scaleX = canvas.width / (img.naturalWidth || canvas.width);
      const scaleY = canvas.height / (img.naturalHeight || canvas.height);

      const scaledOrigin = {
        x: origin.x * scaleX,
        y: origin.y * scaleY
      };

      // Draw X axis (Red)
      ctx.strokeStyle = axes.x_axis.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(scaledOrigin.x, scaledOrigin.y);
      ctx.lineTo(axes.x_axis.x * scaleX, axes.x_axis.y * scaleY);
      ctx.stroke();

      // Draw Y axis (Green)
      ctx.strokeStyle = axes.y_axis.color;
      ctx.beginPath();
      ctx.moveTo(scaledOrigin.x, scaledOrigin.y);
      ctx.lineTo(axes.y_axis.x * scaleX, axes.y_axis.y * scaleY);
      ctx.stroke();

      // Draw Z axis (Blue)
      ctx.strokeStyle = axes.z_axis.color;
      ctx.beginPath();
      ctx.moveTo(scaledOrigin.x, scaledOrigin.y);
      ctx.lineTo(axes.z_axis.x * scaleX, axes.z_axis.y * scaleY);
      ctx.stroke();
    }
  }, [cvData, isLive]);

  // WebSocket effect for live feed only - separate from pre-recorded
  useEffect(() => {
    if (!isLive) return;

    const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + '/ws/view';
    console.log('🔌 Viewer connecting to:', wsUrl);
    const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/view');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Connected to live stream viewer');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Filter by patient_id if provided, otherwise accept all messages
      if (!patientId || data.patient_id === patientId) {
        // Handle raw frame update (immediate passthrough)
        if (data.type === 'live_frame' && data.data?.frame) {
          if (imgRef.current) {
            imgRef.current.src = data.data.frame;
          }
        }

        // Handle CV data update (comes separately, slightly delayed)
        if (data.type === 'cv_data' && data.data) {
          // Merge CV data with existing cvData (preserve frame if present)
          setCvData(prev => ({
            ...prev,
            landmarks: data.data.landmarks,
            head_pose_axes: data.data.head_pose_axes,
            metrics: data.data.metrics
          }));

          // Check for alerts
          if (data.data.metrics?.alert && !alertFired) {
            setAlertFired(true);
            console.log(`🚨 ALERT FIRED for ${data.patient_id}! CRS:`, data.data.metrics.crs_score);
            const audio = new Audio('/alert.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
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

      const timestamp = time.toFixed(1);
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/cv-data/${patient.id}/${timestamp}`)
        .then(res => res.json())
        .then(data => {
          setCvData(data);

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
      className={`relative rounded-t-lg overflow-hidden border-2 transition-all duration-200 ${
        fullscreenMode ? 'h-full' : ''
      } ${
        alertFired
          ? 'border-red-500 shadow-lg shadow-red-500/50'
          : isSelected
          ? 'border-blue-500 shadow-lg shadow-blue-500/30'
          : 'border-slate-700'
      }`}
      animate={alertFired ? { scale: [1, 1.02, 1] } : {}}
      transition={{ repeat: alertFired ? Infinity : 0, duration: 1 }}
    >
      {/* Video Element - Clean, no overlays */}
      {isLive ? (
        <div className={`relative w-full bg-black ${fullscreenMode ? 'h-full' : 'aspect-video'}`}>
          <img
            ref={imgRef}
            className="w-full h-full object-cover"
            alt="Live stream"
            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
          />
          {/* Canvas overlay for landmarks and pose axes */}
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
        <div className={`w-full bg-black flex items-center justify-center text-slate-500 ${fullscreenMode ? 'h-full' : 'aspect-video'}`}>
          No video available
        </div>
      )}

      {/* Alert Pulse Indicator (minimal corner badge) */}
      {alertFired && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-bold"
        >
          🚨 ALERT
        </motion.div>
      )}

      {/* Loading State */}
      {!cvData && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="text-center">
            <div className="text-white text-sm mb-2">
              {isLive ? '⏳ Waiting for live stream...' : 'Loading CV analysis...'}
            </div>
            {isLive && (
              <div className="text-slate-400 text-xs">
                Make sure streaming is active on /stream page
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}

