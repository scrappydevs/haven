'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';
import { motion } from 'framer-motion';

declare global {
  interface Window {
    smplr: any;
  }
}

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const spaceRef = useRef<any>(null);
  const [smplrLoaded, setSmplrLoaded] = useState(false);
  const [spaceReady, setSpaceReady] = useState(false);
  
  useEffect(() => {
    if (!containerRef.current || !smplrLoaded || !window.smplr || spaceRef.current) return;
    
    const initViewer = async () => {
      try {
        console.log('🎬 Initializing landing page viewer...');
        
        // Fetch Smplrspace config
        const configRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/smplrspace/config`);
        const config = await configRes.json();
        
        // Initialize viewer
        const space = new window.smplr.Space({
          spaceId: config.spaceId,
          clientToken: config.clientToken,
          containerId: 'landing-smplr-container'
        });
        
        spaceRef.current = space;
        
        await space.startViewer({
          preview: false,
          mode: '3d',
          allowModeChange: false,
          hideNavigationButtons: true,  // Hide toolbar
          onReady: async () => {
            console.log('✅ Landing viewer ready');
            setSpaceReady(true);
            
            // Set camera for beautiful overview
            space.setCameraPlacement({
              alpha: -Math.PI / 6,
              beta: Math.PI / 4,
              radius: 35,
              target: { x: 20, y: 0, z: 0 },
              animationDuration: 2
            });
            
            // Fetch and color rooms with alerts
            try {
              const roomsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms`);
              const rooms = await roomsRes.json();
              
              // Simulate alerts for visual interest (mix of colors)
              const criticalRooms = [0];  // Room 1: Critical (red)
              const warningRooms = [1];   // Room 2: Warning (orange)
              // Rooms 3-5 will be green (occupied) or gray (empty)
              
              // Add colored room polygons
              const roomPolygons = rooms
                .filter((r: any) => r.metadata?.polygon && r.room_type === 'patient')
                .map((room: any, idx: number) => ({
                  id: room.room_id,
                  coordinates: room.metadata.polygon,
                  levelIndex: 0,
                  alertLevel: criticalRooms.includes(idx) ? 'critical' : 
                             warningRooms.includes(idx) ? 'warning' : 'none',
                  occupied: idx >= 2 || !!room.patient_id // Assume rooms 3+ occupied for demo
                }));
              
              if (roomPolygons.length > 0) {
                space.addDataLayer({
                  id: 'room-colors',
                  type: 'polygon',
                  data: roomPolygons,
                  color: (data: any) => {
                    if (data.alertLevel === 'critical') return '#ef4444'; // Red
                    if (data.alertLevel === 'warning') return '#f97316';  // Orange
                    if (data.occupied) return '#10b981';  // Green
                    return '#e5e7eb';  // Gray
                  },
                  alpha: 0.4,
                  height: 0.1
                });
              }
            } catch (err) {
              console.log('Could not fetch rooms for landing page');
            }
            
            // Smooth continuous rotation using requestAnimationFrame
            let lastUpdate = Date.now();
            const rotationSpeed = 0.0002; // radians per millisecond
            
            const animate = () => {
              if (spaceRef.current) {
                const now = Date.now();
                const delta = now - lastUpdate;
                lastUpdate = now;
                
                const current = spaceRef.current.getCameraPlacement();
                spaceRef.current.setCameraPlacement({
                  ...current,
                  alpha: current.alpha + (rotationSpeed * delta),
                  animationDuration: 0
                });
                
                requestAnimationFrame(animate);
              }
            };
            
            requestAnimationFrame(animate);
          },
          onError: (error: string) => {
            console.error('Viewer error:', error);
            setSpaceReady(true);
          }
        });
      } catch (error) {
        console.error('Failed to initialize viewer:', error);
        setSpaceReady(true);
      }
    };
    
    initViewer();
    
    return () => {
      if (spaceRef.current) {
        spaceRef.current.remove();
        spaceRef.current = null;
      }
    };
  }, [smplrLoaded]);
  
  return (
    <div className="relative w-full h-screen overflow-hidden bg-white">
      {/* Smplr.js Script */}
      <Script
        src="https://app.smplrspace.com/lib/smplr.js"
        onLoad={() => setSmplrLoaded(true)}
        strategy="afterInteractive"
      />
      <link href="https://app.smplrspace.com/lib/smplr.css" rel="stylesheet" />
      
      {/* 3D Floor Plan - Visible Background */}
      <div 
        id="landing-smplr-container" 
        ref={containerRef}
        className="absolute inset-0 w-full h-full"
      />
      
      {/* Hide Smplrspace toolbar */}
      <style jsx global>{`
        #landing-smplr-container .smplr-toolbar {
          display: none !important;
        }
        #landing-smplr-container .smplr-controls {
          display: none !important;
        }
      `}</style>
      
      {/* Very subtle overlay for text contrast */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-white/10 pointer-events-none z-10" />
      
      {/* Content */}
      <div className="relative z-20 flex flex-col items-center justify-center h-full pointer-events-none">
        {/* Subtle blur container for text */}
        <div className="backdrop-blur-sm bg-white/30 px-16 py-12 rounded-lg border border-white/40 shadow-2xl">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-center mb-8"
          >
            <h1 className="text-7xl font-light text-neutral-950 mb-3 tracking-tight uppercase">
              Haven
            </h1>
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="text-xs font-light text-neutral-600 uppercase tracking-wider"
            >
              Intelligent Patient Care and Hospital Management
            </motion.p>
          </motion.div>
          
          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1 }}
            className="pointer-events-auto text-center"
          >
            <a
              href="/dashboard"
              className="px-8 py-3 bg-primary-700 hover:bg-primary-800 text-white font-light uppercase tracking-wider transition-all text-xs inline-block"
            >
              Enter System
            </a>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
