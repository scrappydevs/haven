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
}

interface CVData {
  crs_score: number;
  heart_rate: number;
  respiratory_rate: number;
  alert?: boolean;
  head_pitch?: number;
  head_yaw?: number;
  head_roll?: number;
  eye_openness?: number;
  attention_score?: number;
}

export default function VideoPlayer({ patient, isLive = false, isSelected = false, onCvDataUpdate }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
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
      console.log('📥 Received WebSocket data:', data.type, data.patient_id);

      if (data.type === 'live_frame' && data.patient_id === 'live-1') {
        if (imgRef.current && data.data?.frame) {
          imgRef.current.src = data.data.frame;
          console.log('🖼️ Updated live frame, CRS:', data.data.crs_score, 'HR:', data.data.heart_rate);
        }

        setCvData(data.data);

        if (data.data.alert && !alertFired) {
          setAlertFired(true);
          console.log('🚨 ALERT FIRED! CRS:', data.data.crs_score);
          const audio = new Audio('/alert.mp3');
          audio.play().catch(e => console.log('Audio play failed:', e));
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

          if (data.alert && !alertFired) {
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
        <img
          ref={imgRef}
          className="w-full aspect-video object-cover bg-black"
          alt="Live stream"
          src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        />
      ) : patient.id <= 5 ? (
        <video
          ref={videoRef}
          src={`/videos/patient-${patient.id}.mp4`}
          autoPlay
          loop
          muted
          playsInline
          className="w-full aspect-video object-cover"
        />
      ) : (
        <div className="w-full aspect-video bg-black flex items-center justify-center text-slate-500">
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

