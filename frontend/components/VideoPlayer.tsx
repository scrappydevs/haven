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
}

interface CVData {
  crs_score: number;
  heart_rate: number;
  respiratory_rate: number;
  alert?: boolean;
}

export default function VideoPlayer({ patient, isLive = false }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [cvData, setCvData] = useState<CVData | null>(null);
  const [alertFired, setAlertFired] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (isLive) {
      // Connect to WebSocket for live stream
      const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + '/ws/view';
      const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/view');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Connected to live stream viewer');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'live_frame' && data.patient_id === 'live-1') {
          // Update image with new frame
          if (imgRef.current) {
            imgRef.current.src = data.data.frame;
          }

          // Update CV metrics
          setCvData(data.data);

          // Fire alert if CRS detected
          if (data.data.alert && !alertFired) {
            setAlertFired(true);
            const audio = new Audio('/alert.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('❌ Disconnected from live stream');
      };

      return () => {
        ws.close();
      };
    }

    // Pre-recorded video handling
    const video = videoRef.current;
    if (!video) return;

    const interval = setInterval(() => {
      const time = video.currentTime;
      setCurrentTime(time);

      // Fetch CV data for current timestamp
      const timestamp = time.toFixed(1);
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/cv-data/${patient.id}/${timestamp}`)
        .then(res => res.json())
        .then(data => {
          setCvData(data);

          // Fire alert if CRS detected
          if (data.alert && !alertFired) {
            setAlertFired(true);
            // Play alert sound if available
            const audio = new Audio('/alert.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
          }
        })
        .catch(err => console.error('Error fetching CV data:', err));
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, [patient.id, isLive, alertFired]);

  return (
    <motion.div
      className={`relative rounded-lg overflow-hidden border-2 transition-colors ${
        alertFired ? 'border-red-500 shadow-lg shadow-red-500/50' : 'border-slate-700'
      }`}
      animate={alertFired ? { scale: [1, 1.02, 1] } : {}}
      transition={{ repeat: alertFired ? Infinity : 0, duration: 1 }}
    >
      {/* Video Element */}
      {isLive ? (
        <img
          ref={imgRef}
          className="w-full aspect-video object-cover bg-black"
          alt="Live stream"
        />
      ) : (
        <video
          ref={videoRef}
          src={`/videos/patient-${patient.id}.mp4`}
          autoPlay
          loop
          muted
          playsInline
          className="w-full aspect-video object-cover"
        />
      )}

      {/* Patient Info Overlay */}
      <div className="absolute top-2 left-2 bg-black/70 backdrop-blur px-3 py-2 rounded-lg">
        <p className="text-white font-semibold text-sm">{patient.name}</p>
        <p className="text-slate-300 text-xs">
          {isLive ? '🔴 LIVE' : `Patient #${patient.id}`}
        </p>
      </div>

      {/* CV Metrics Overlay */}
      {cvData && (
        <div className="absolute bottom-2 left-2 right-2 bg-black/70 backdrop-blur p-2 rounded-lg">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <p className="text-slate-400">Heart Rate</p>
              <p className="text-white font-bold">{cvData.heart_rate} bpm</p>
            </div>
            <div>
              <p className="text-slate-400">CRS Risk</p>
              <p className={`font-bold ${
                cvData.crs_score > 0.7 ? 'text-red-400' :
                cvData.crs_score > 0.4 ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {(cvData.crs_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            RR: {cvData.respiratory_rate} breaths/min
          </div>
        </div>
      )}

      {/* Alert Banner */}
      {alertFired && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="absolute top-0 left-0 right-0 bg-red-500 text-white px-3 py-2 text-center font-bold text-sm"
        >
          🚨 CRS Grade 2 Detected
        </motion.div>
      )}

      {/* Loading State (when no CV data yet) */}
      {!cvData && !isLive && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/30">
          <div className="text-white text-sm">Loading CV analysis...</div>
        </div>
      )}
    </motion.div>
  );
}

