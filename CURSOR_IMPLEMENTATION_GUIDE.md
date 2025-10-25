# TrialSentinel AI - Implementation Guide for Cursor

**Context**: This is a CalHacks 12.0 hackathon project. Real-time computer vision monitoring for clinical trial safety.

**Goal**: Build a dashboard showing patient video feeds with live CV analysis, plus live webcam streaming between two computers.

**Tech Stack**: Next.js 15, React 19, TypeScript, Tailwind CSS, FastAPI backend with WebSocket support

---

## 📋 Implementation Phases

### **Phase 1**: Basic Dashboard (6 video feeds) - **Priority: CRITICAL**
### **Phase 2**: Live Streaming (Computer 1 → Computer 2) - **Priority: HIGH**

---

# PHASE 1: Basic Dashboard

## Overview

Build a dashboard that shows 6 patient video feeds in a 3x2 grid. Each video displays:
- Patient name and ID
- Real-time CV metrics (heart rate, CRS risk score)
- Alerts when CRS detected (red border, banner)

**Visual Reference**:
```
┌─────────────────────────────────────────────────────┐
│  TrialSentinel AI | 47 Patients | 2 Active Alerts   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Video 1]    [Video 2]    [Video 3]                │
│   Sarah Chen   Mike Torres Emma Wilson              │
│   HR: 78       HR: 82      HR: 75                   │
│   CRS: 15%     CRS: 22%    CRS: 12%                 │
│                                                      │
│  [Video 4]    [Video 5]    [Video 6]                │
│   David Kim    Linda Wu    James A.                 │
│   HR: 85       HR: 118 🚨  HR: 79                   │
│   CRS: 18%     CRS: 73%    CRS: 16%                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Step 1: Initialize Next.js Frontend (5 minutes)

### 1.1 Create Next.js App

```bash
cd frontend

# Initialize Next.js with all required options
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*" --no-turbopack

# When prompted:
# ✅ TypeScript: Yes
# ✅ ESLint: Yes
# ✅ Tailwind CSS: Yes
# ✅ `app/` directory: Yes
# ❌ `src/` directory: No
# ✅ Import alias: Yes (@/*)
# ❌ Turbopack: No

# Install additional dependencies
npm install framer-motion recharts lucide-react

# Install shadcn/ui
npx shadcn-ui@latest init
# Select: Default style, Slate color, Yes to CSS variables

# Add required shadcn components
npx shadcn-ui@latest add button card badge dialog toast
```

### 1.2 Configure Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Step 2: Create Dashboard Layout (10 minutes)

### 2.1 Update Root Layout

**File**: `frontend/app/layout.tsx`

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TrialSentinel AI - Clinical Trial Monitoring",
  description: "Real-time computer vision monitoring for clinical trial safety",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
```

### 2.2 Update Global Styles

**File**: `frontend/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222 47% 11%;
    --foreground: 0 0% 100%;
    --card: 222 47% 15%;
    --card-foreground: 0 0% 100%;
    --primary: 217 91% 60%;
    --primary-foreground: 0 0% 100%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
  }
}

body {
  @apply bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white;
}
```

---

## Step 3: Create Dashboard Page (30 minutes)

### 3.1 Main Dashboard Component

**File**: `frontend/app/dashboard/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import AlertPanel from '@/components/AlertPanel';
import StatsBar from '@/components/StatsBar';

interface Patient {
  id: number;
  name: string;
  age: number;
  condition: string;
  baseline_vitals: {
    heart_rate: number;
  };
}

interface Alert {
  patient_id: number;
  message: string;
  crs_score: number;
  heart_rate: number;
  timestamp: string;
}

export default function DashboardPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState({
    patients_monitored: 47,
    active_alerts: 0,
    daily_cost_savings: 17550
  });

  useEffect(() => {
    // Fetch patients from backend
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients`)
      .then(res => res.json())
      .then(data => setPatients(data))
      .catch(err => console.error('Error fetching patients:', err));

    // Poll for alerts every 2 seconds
    const alertInterval = setInterval(() => {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/alerts`)
        .then(res => res.json())
        .then(data => setAlerts(data))
        .catch(err => console.error('Error fetching alerts:', err));
    }, 2000);

    // Fetch stats
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Error fetching stats:', err));

    return () => clearInterval(alertInterval);
  }, []);

  // Display first 6 patients for demo
  const displayedPatients = patients.slice(0, 6);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <span className="text-2xl">👁️</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">TrialSentinel AI</h1>
                <p className="text-sm text-slate-400">Linvoseltamab Phase III - NCT04649359</p>
              </div>
            </div>

            {/* Stats */}
            <StatsBar stats={stats} alertCount={alerts.length} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Video Grid (Left - 8 columns) */}
          <div className="col-span-8">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">Patient Monitoring</h2>
              <p className="text-sm text-slate-400">Real-time video feeds with CV analysis</p>
            </div>

            {displayedPatients.length > 0 ? (
              <div className="grid grid-cols-3 gap-4">
                {displayedPatients.map(patient => (
                  <VideoPlayer key={patient.id} patient={patient} />
                ))}
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-12 text-center">
                <p className="text-slate-400">Loading patients...</p>
              </div>
            )}
          </div>

          {/* Alert Panel (Right - 4 columns) */}
          <div className="col-span-4">
            <AlertPanel alerts={alerts} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 4: Create VideoPlayer Component (45 minutes)

**File**: `frontend/components/VideoPlayer.tsx`

```typescript
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

  useEffect(() => {
    if (isLive) {
      // Live stream handling - will implement in Phase 2
      return;
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
```

---

## Step 5: Create Supporting Components (30 minutes)

### 5.1 Alert Panel Component

**File**: `frontend/components/AlertPanel.tsx`

```typescript
'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface Alert {
  patient_id: number;
  timestamp: string;
  message: string;
  crs_score: number;
  heart_rate: number;
  severity?: string;
}

interface AlertPanelProps {
  alerts: Alert[];
}

export default function AlertPanel({ alerts }: AlertPanelProps) {
  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 p-4 h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white">Live Alerts</h2>
        <div className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-semibold">
          {alerts.length} Active
        </div>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-250px)] overflow-y-auto">
        <AnimatePresence>
          {alerts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <div className="text-6xl mb-4">✅</div>
              <p className="text-slate-400 text-sm">No active alerts</p>
              <p className="text-slate-500 text-xs mt-2">All patients stable</p>
            </motion.div>
          ) : (
            alerts.map((alert, idx) => (
              <motion.div
                key={`${alert.patient_id}-${alert.timestamp}`}
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-red-500/10 border border-red-500/30 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-xl">🚨</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-semibold text-sm truncate">
                      {alert.message}
                    </p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-300">
                      <span>CRS: {(alert.crs_score * 100).toFixed(0)}%</span>
                      <span>•</span>
                      <span>HR: {alert.heart_rate} bpm</span>
                    </div>
                    <p className="text-slate-400 text-xs mt-2">
                      {new Date().toLocaleTimeString()}
                    </p>
                  </div>
                </div>

                <div className="mt-3 flex gap-2">
                  <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-xs py-2 rounded-lg font-semibold transition-colors">
                    Dispatch Nurse
                  </button>
                  <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs py-2 rounded-lg font-semibold transition-colors">
                    View Details
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

### 5.2 Stats Bar Component

**File**: `frontend/components/StatsBar.tsx`

```typescript
interface StatsBarProps {
  stats: {
    patients_monitored: number;
    daily_cost_savings: number;
  };
  alertCount: number;
}

export default function StatsBar({ stats, alertCount }: StatsBarProps) {
  return (
    <div className="flex gap-6">
      <StatCard
        label="Patients Monitored"
        value={stats.patients_monitored.toString()}
        color="blue"
      />
      <StatCard
        label="Active Alerts"
        value={alertCount.toString()}
        color={alertCount > 0 ? "red" : "green"}
      />
      <StatCard
        label="Daily Savings"
        value={`$${(stats.daily_cost_savings / 1000).toFixed(1)}K`}
        color="green"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  color: "blue" | "red" | "green";
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    red: "bg-red-500/10 text-red-400 border-red-500/30",
    green: "bg-green-500/10 text-green-400 border-green-500/30",
  };

  return (
    <div className={`px-4 py-2 rounded-lg border ${colorClasses[color]}`}>
      <p className="text-xs opacity-80">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}
```

---

## Step 6: Test Phase 1 (10 minutes)

### 6.1 Start Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate patient data
python scripts/generate_patients.py

# Start server
uvicorn app.main:app --reload
```

Verify: http://localhost:8000/patients should return 47 patients

### 6.2 Start Frontend

```bash
cd frontend
npm run dev
```

Open: http://localhost:3000/dashboard

### 6.3 Expected Behavior

✅ Dashboard loads with header
✅ Shows "Loading patients..." initially
✅ After ~1 second, shows 6 empty video placeholders
✅ Alert panel shows "No active alerts"
✅ Stats show: 47 patients, 0 alerts, $17.5K savings

**Note**: Videos won't play yet (need to add video files in Phase 1.5)

---

## Phase 1.5: Add Test Videos (OPTIONAL - for testing)

If you want to test without filming real videos:

```bash
# Create dummy videos using FFmpeg (if installed)
cd frontend/public
mkdir videos

# Generate 3-second test videos with colored backgrounds
ffmpeg -f lavfi -i color=c=blue:s=640x480:d=3 -pix_fmt yuv420p videos/patient-1.mp4
ffmpeg -f lavfi -i color=c=green:s=640x480:d=3 -pix_fmt yuv420p videos/patient-2.mp4
# ... repeat for patient-3 through patient-6
```

Or: Use any short MP4 files and rename them `patient-1.mp4` through `patient-6.mp4`

---

# PHASE 2: Live Streaming

## Overview

Add live webcam streaming so Computer 1 can stream to Computer 2's dashboard.

**Architecture**:
```
Computer 1                Backend                Computer 2
(Webcam)                  (WebSocket)            (Dashboard)
    │                         │                      │
    │  1. Capture frame       │                      │
    │─────────────────────────>│                      │
    │                         │  2. Process CV       │
    │                         │                      │
    │                         │  3. Broadcast        │
    │                         │─────────────────────>│
    │                         │                      │
    │                         │  4. Display feed     │
    │                         │     + metrics        │
```

---

## Step 7: Add WebSocket Support to Backend (30 minutes)

### 7.1 Install WebSocket Dependencies

```bash
cd backend
pip install websockets
pip freeze > requirements.txt
```

### 7.2 Create WebSocket Manager

**File**: `backend/app/websocket.py`

```python
"""
WebSocket manager for live video streaming
Handles connections from streamers (webcam computers) and viewers (dashboards)
"""

from fastapi import WebSocket
from typing import List, Dict
import base64
import cv2
import numpy as np
import mediapipe as mp
import json

# Initialize MediaPipe Face Mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class ConnectionManager:
    def __init__(self):
        self.streamers: List[WebSocket] = []  # Computers sending video
        self.viewers: List[WebSocket] = []    # Dashboards watching

    async def connect_streamer(self, websocket: WebSocket):
        await websocket.accept()
        self.streamers.append(websocket)
        print(f"✅ Streamer connected. Total streamers: {len(self.streamers)}")

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)
        print(f"✅ Viewer connected. Total viewers: {len(self.viewers)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.streamers:
            self.streamers.remove(websocket)
            print(f"❌ Streamer disconnected. Remaining: {len(self.streamers)}")
        if websocket in self.viewers:
            self.viewers.remove(websocket)
            print(f"❌ Viewer disconnected. Remaining: {len(self.viewers)}")

    async def broadcast_frame(self, frame_data: Dict):
        """Send processed frame to all viewers"""
        disconnected = []
        for viewer in self.viewers:
            try:
                await viewer.send_json(frame_data)
            except:
                disconnected.append(viewer)

        # Remove disconnected viewers
        for viewer in disconnected:
            self.disconnect(viewer)

manager = ConnectionManager()

def process_frame(frame_base64: str) -> Dict:
    """
    Process video frame with computer vision

    Args:
        frame_base64: Base64 encoded JPEG image

    Returns:
        {
            "frame": base64_string,
            "crs_score": 0.45,
            "heart_rate": 78,
            "respiratory_rate": 14,
            "alert": False
        }
    """
    try:
        # Decode base64 to OpenCV image
        if ',' in frame_base64:
            frame_base64 = frame_base64.split(',')[1]

        img_data = base64.b64decode(frame_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Failed to decode frame")

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run face detection
        results = face_mesh.process(rgb_frame)

        # Default values
        crs_score = 0.0
        heart_rate = 75
        respiratory_rate = 14

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]

            # Detect facial flushing (CRS indicator)
            # Sample cheek regions: landmarks 205 (left) and 425 (right)
            cheek_redness = 0.0

            for idx in [205, 425]:
                lm = landmarks.landmark[idx]
                x, y = int(lm.x * w), int(lm.y * h)

                # Extract 20x20 pixel region around landmark
                roi = frame[max(0, y-10):min(h, y+10), max(0, x-10):min(w, x+10)]

                if roi.size > 0:
                    # Calculate redness: R channel minus average of G and B
                    r = np.mean(roi[:, :, 2])
                    g = np.mean(roi[:, :, 1])
                    b = np.mean(roi[:, :, 0])
                    cheek_redness += (r - (g + b) / 2) / 255.0

            # Average both cheeks
            cheek_redness /= 2

            # Calculate CRS risk score (0-1 scale)
            crs_score = min(1.0, max(0.0, cheek_redness * 2.5))

            # Simulate heart rate increase with CRS
            # In real system, would use rPPG over multiple frames
            heart_rate = int(75 + (crs_score * 30))  # 75-105 bpm range
            respiratory_rate = int(14 + (crs_score * 10))  # 14-24 breaths/min

            # Draw face landmarks (makes it look impressive!)
            for landmark in landmarks.landmark:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # Encode frame back to base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64_out = base64.b64encode(buffer).decode('utf-8')

        return {
            "frame": f"data:image/jpeg;base64,{frame_base64_out}",
            "crs_score": round(crs_score, 2),
            "heart_rate": heart_rate,
            "respiratory_rate": respiratory_rate,
            "alert": crs_score > 0.7
        }

    except Exception as e:
        print(f"❌ Error processing frame: {e}")
        return {
            "frame": frame_base64,
            "crs_score": 0.0,
            "heart_rate": 75,
            "respiratory_rate": 14,
            "alert": False,
            "error": str(e)
        }
```

### 7.3 Add WebSocket Endpoints to Main App

**File**: `backend/app/main.py` (add these endpoints)

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket import manager, process_frame

# Add after existing endpoints

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for computers streaming webcam
    Receives frames, processes with CV, broadcasts to viewers
    """
    await manager.connect_streamer(websocket)
    try:
        while True:
            # Receive frame from streamer
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                # Process frame with computer vision
                result = process_frame(data.get("frame"))

                # Broadcast to all dashboard viewers
                await manager.broadcast_frame({
                    "type": "live_frame",
                    "patient_id": "live-1",
                    "data": result
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Streamer disconnected")

@app.websocket("/ws/view")
async def websocket_view(websocket: WebSocket):
    """
    WebSocket endpoint for dashboards viewing live stream
    Receives processed frames from backend
    """
    await manager.connect_viewer(websocket)
    try:
        while True:
            # Keep connection alive, wait for messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Viewer disconnected")
```

---

## Step 8: Create Webcam Streamer Page (30 minutes)

**File**: `frontend/app/stream/page.tsx`

```typescript
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
      const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/stream');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Connected to WebSocket server');
        setIsStreaming(true);
        startCapture();
      };

      ws.onclose = () => {
        console.log('❌ Disconnected from server');
        setIsStreaming(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Failed to connect to server');
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

    const captureFrame = () => {
      if (!isStreaming || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
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
      } catch (error) {
        console.error('Error sending frame:', error);
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
```

---

## Step 9: Update VideoPlayer for Live Streaming (15 minutes)

**File**: `frontend/components/VideoPlayer.tsx` (add live streaming support)

Add this to the existing `useEffect` hook:

```typescript
useEffect(() => {
  if (isLive) {
    // Connect to WebSocket for live stream
    const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') + '/ws/view';
    const ws = new WebSocket(wsUrl || 'ws://localhost:8000/ws/view');

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

  // ... rest of existing pre-recorded video code
}, [isLive, alertFired]);
```

---

## Step 10: Update Dashboard to Show Live Feed (10 minutes)

**File**: `frontend/app/dashboard/page.tsx` (modify displayed patients)

Replace the `displayedPatients` line with:

```typescript
// Display first 5 pre-recorded + 1 live feed
const displayedPatients = [
  ...patients.slice(0, 5),
  {
    id: 999,  // Special ID for live feed
    name: "LIVE DEMO",
    age: 0,
    condition: "Live Webcam Stream",
    baseline_vitals: { heart_rate: 75 }
  }
];
```

Update the video grid to pass `isLive` prop:

```typescript
<div className="grid grid-cols-3 gap-4">
  {displayedPatients.map((patient, index) => (
    <VideoPlayer
      key={patient.id}
      patient={patient}
      isLive={index === 5}  // 6th video is live
    />
  ))}
</div>
```

---

## Step 11: Test Phase 2 (15 minutes)

### 11.1 Restart Backend (to load WebSocket code)

```bash
cd backend
# If backend is already running, stop it (Ctrl+C)
uvicorn app.main:app --reload
```

### 11.2 Test Streaming Flow

**Computer 1 (or same computer, different tab)**:
1. Open: http://localhost:3000/stream
2. Click "Start Streaming"
3. Allow camera permissions
4. Should see yourself on camera
5. Should see "LIVE" indicator and FPS counter

**Computer 2 (or same computer, different tab)**:
1. Open: http://localhost:3000/dashboard
2. Look at 6th video (bottom-right)
3. Should say "LIVE DEMO"
4. After a few seconds, should see your face!
5. Should see CV metrics updating (HR, CRS score)

### 11.3 Test Alert

On Computer 1 (streaming):
1. Rub your cheeks to make them red
2. Look at Computer 2 dashboard
3. Within 5-10 seconds, CRS score should increase
4. If score goes above 70%, alert should fire! 🚨

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- ✅ Dashboard loads without errors
- ✅ Shows 6 video players in grid
- ✅ Alert panel on right side
- ✅ Stats bar shows correct numbers
- ✅ Videos play (if added)
- ✅ CV metrics display below videos

### Phase 2 Complete When:
- ✅ Stream page accessible at `/stream`
- ✅ Webcam starts successfully
- ✅ FPS counter shows ~30 FPS
- ✅ Dashboard shows live feed in 6th slot
- ✅ Face landmarks visible on live feed
- ✅ CV metrics update in real-time
- ✅ Alert fires when face gets red

---

## 🐛 Troubleshooting

### Backend Issues

**"Module 'websockets' not found"**
```bash
pip install websockets
```

**"Port 8000 already in use"**
```bash
lsof -i :8000
kill -9 <PID>
```

### Frontend Issues

**"Cannot connect to API"**
- Check backend is running: http://localhost:8000/docs
- Check `.env.local` has correct API URL
- Try: `NEXT_PUBLIC_API_URL=http://localhost:8000`

**"WebSocket connection failed"**
- Make sure backend has WebSocket endpoints
- Check browser console for error messages
- Verify URL: `ws://localhost:8000/ws/stream` (not `http://`)

**Videos not playing**
- Check files exist in `frontend/public/videos/`
- Files named: `patient-1.mp4` through `patient-6.mp4`
- Try different video format (H.264 MP4 works best)

### Live Streaming Issues

**Camera not working**
- Allow camera permissions in browser
- Try Chrome (best WebRTC support)
- Check camera works in other apps

**Lag/low FPS**
- Reduce resolution in stream page: `width: 640, height: 480`
- Lower frame rate: `setTimeout(captureFrame, 100)` (10 FPS instead of 30)
- Make sure both computers on same WiFi network

**Alert not firing**
- Rub cheeks harder (need visible redness)
- Check CRS score in dashboard (should be >70%)
- Check browser console for errors

---

## 📝 Next Steps After Implementation

1. **Add video files**: Film 6 patient videos (see main README)
2. **Pre-compute CV data**: Run `backend/scripts/precompute_cv.py`
3. **Add alert sound**: Place `alert.mp3` in `frontend/public/`
4. **Test on two computers**: Make sure live streaming works across network
5. **Polish animations**: Adjust Framer Motion timings
6. **Add more metrics**: Respiratory rate graph, patient history, etc.

---

## 🎯 Time Estimates

| Phase | Task | Time |
|-------|------|------|
| 1 | Initialize Next.js | 5 min |
| 1 | Dashboard layout | 10 min |
| 1 | Dashboard page | 30 min |
| 1 | VideoPlayer component | 45 min |
| 1 | Supporting components | 30 min |
| 1 | Testing | 10 min |
| **Phase 1 Total** | | **2 hours 10 min** |
| 2 | Backend WebSocket | 30 min |
| 2 | Stream page | 30 min |
| 2 | Update VideoPlayer | 15 min |
| 2 | Update Dashboard | 10 min |
| 2 | Testing | 15 min |
| **Phase 2 Total** | | **1 hour 40 min** |
| **GRAND TOTAL** | | **3 hours 50 min** |

---

## ✅ Final Checklist

### Phase 1:
- [ ] Next.js initialized with TypeScript + Tailwind
- [ ] Dependencies installed (framer-motion, recharts, etc.)
- [ ] Dashboard page created (`/dashboard`)
- [ ] VideoPlayer component working
- [ ] AlertPanel component working
- [ ] StatsBar component working
- [ ] Backend serving patient data
- [ ] Frontend fetches and displays data

### Phase 2:
- [ ] WebSocket dependencies installed
- [ ] `websocket.py` created with manager
- [ ] WebSocket endpoints added to backend
- [ ] Stream page created (`/stream`)
- [ ] Webcam capture working
- [ ] Live feed shows on dashboard
- [ ] CV processing in real-time
- [ ] Alerts fire when CRS detected

---

**This implementation guide is complete and ready for Cursor to execute! Each step has exact code, file paths, and explanations.** 🚀
   