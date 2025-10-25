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
  onCvDataUpdate?: (data: CVData | null) => void;
  isSelected?: boolean;
}

interface CVData {
  crs_score: number;
  heart_rate: number;
  respiratory_rate: number;
  alert?: boolean;
}

export default function VideoPlayer({ patient, isLive = false, onCvDataUpdate, isSelected = false }: VideoPlayerProps) {
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
      console.log('🔌 Viewer connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/view');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Connected to live stream viewer');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📥 Received WebSocket data:', data.type, data.patient_id, 'Full data:', data);

        if (data.type === 'live_frame' && data.patient_id === 'live-1') {
          // Update image with new frame
          if (imgRef.current && data.data?.frame) {
            imgRef.current.src = data.data.frame;
            console.log('🖼️ Updated live frame, CRS:', data.data.crs_score, 'HR:', data.data.heart_rate);
          } else {
            console.error('❌ Missing frame data or imgRef');
          }

          // Update CV metrics
          setCvData(data.data);

          // Fire alert if CRS detected
          if (data.data.alert && !alertFired) {
            setAlertFired(true);
            console.log('🚨 ALERT FIRED! CRS:', data.data.crs_score);
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

  // Notify parent of CV data updates
  useEffect(() => {
    if (onCvDataUpdate) {
      onCvDataUpdate(cvData);
    }
  }, [cvData, onCvDataUpdate]);

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

