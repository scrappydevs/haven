'use client';

import { useEffect, useRef, useState } from 'react';

export default function StreamPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [fps, setFps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const startStreaming = async () => {
    try {
      setError(null);

      // Request webcam access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        }
      });

      // Display in video element
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Connect to WebSocket
      const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + '/ws/stream';
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/stream');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Connected to WebSocket server');
        setIsStreaming(true);
        startCapture();
      };

      ws.onclose = (event) => {
        console.log('❌ Disconnected from server. Code:', event.code, 'Reason:', event.reason);
        setIsStreaming(false);
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('Failed to connect to server. Make sure backend is running on port 8000.');
      };

    } catch (err) {
      console.error('Error accessing webcam:', err);
      setError('Could not access webcam. Please allow camera permissions.');
    }
  };

  const startCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameCount = 0;
    let lastFpsUpdate = Date.now();
    let isActive = true;  // Local flag instead of state

    const captureFrame = () => {
      if (!isActive || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.log('⏹️ Stopping capture. Active:', isActive, 'WS state:', wsRef.current?.readyState);
        return;
      }

      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current video frame to canvas
      ctx.drawImage(video, 0, 0);

      // Convert canvas to base64 JPEG
      const frameData = canvas.toDataURL('image/jpeg', 0.8);

      // Send to backend via WebSocket
      try {
        wsRef.current.send(JSON.stringify({
          type: 'frame',
          frame: frameData
        }));
        
        // Log every 30th frame (once per second at 30fps)
        if (frameCount % 30 === 0) {
          console.log('📤 Sent frame to backend, size:', frameData.length, 'bytes');
        }
      } catch (error) {
        console.error('❌ Error sending frame:', error);
        isActive = false;
        return;
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
      setTimeout(captureFrame, 33);
    };

    captureFrame();
    
    // Return cleanup function
    return () => {
      isActive = false;
    };
  };

  const stopStreaming = () => {
    setIsStreaming(false);

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop all media tracks
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            📹 Webcam Streamer
          </h1>
          <p className="text-slate-400">
            Stream your webcam to the dashboard for live CV analysis
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Video Preview */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6">
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden mb-4">
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              autoPlay
              muted
              playsInline
            />

            {/* Status Overlay */}
            <div className="absolute top-4 right-4 px-4 py-2 rounded-lg bg-black/70 backdrop-blur">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  isStreaming ? 'bg-red-500 animate-pulse' : 'bg-gray-500'
                }`} />
                <span className="text-white font-semibold">
                  {isStreaming ? 'LIVE' : 'OFFLINE'}
                </span>
              </div>
            </div>

            {/* FPS Counter */}
            {isStreaming && (
              <div className="absolute top-4 left-4 px-3 py-1 rounded bg-black/70 backdrop-blur">
                <span className="text-green-400 font-mono text-sm">
                  {fps} FPS
                </span>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="flex gap-4">
            {!isStreaming ? (
              <button
                onClick={startStreaming}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                🎥 Start Streaming
              </button>
            ) : (
              <button
                onClick={stopStreaming}
                className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                ⏹️ Stop Streaming
              </button>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-3">📋 How to Use</h2>
          <ol className="space-y-2 text-slate-300 text-sm">
            <li>1. Click "Start Streaming" button above</li>
            <li>2. Allow camera permissions when prompted</li>
            <li>3. On another computer, open the dashboard</li>
            <li>4. Look for "LIVE DEMO" patient (6th video feed)</li>
            <li>5. Try rubbing your face to simulate CRS → Alert fires!</li>
          </ol>

          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-blue-400 text-sm">
              💡 <strong>Tip:</strong> Make sure both computers are on the same network and backend is running!
            </p>
          </div>
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />
      </div>
    </div>
  );
}

