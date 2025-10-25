'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';
import FloorPlanLegend from '@/components/FloorPlanLegend';
import RoomDetailsPanel from '@/components/RoomDetailsPanel';

// Declare smplr global type
declare global {
  interface Window {
    smplr: any;
  }
}

interface Room {
  id: string;
  name: string;
  type: 'patient' | 'nurse_station' | 'other';
  position: {
    levelIndex: number;
    x: number;
    z: number;
    polygon?: any[];
  };
  assignedPatient?: AssignedPatient;
  assignedNurses?: AssignedNurse[];
}

interface AssignedPatient {
  patient_id: string;
  name: string;
  age: number;
  condition: string;
  photo_url: string;
}

interface AssignedNurse {
  id: string;
  name: string;
  shift: string;
}

interface SupabasePatient {
  id: string;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  photo_url: string;
  condition: string;
}

export default function FloorPlanPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const spaceRef = useRef<any>(null);
  const [isViewerReady, setIsViewerReady] = useState(false);
  const [viewerError, setViewerError] = useState<string | null>(null);
  const [useDemoMode, setUseDemoMode] = useState(false);
  const [smplrLoaded, setSmplrLoaded] = useState(false);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [showNurseModal, setShowNurseModal] = useState(false);
  const [availablePatients, setAvailablePatients] = useState<SupabasePatient[]>([]);
  const [roomsLoaded, setRoomsLoaded] = useState(false);
  const [roomsListCollapsed, setRoomsListCollapsed] = useState(false);
  const [patientsListCollapsed, setPatientsListCollapsed] = useState(false);
  const [draggedPatient, setDraggedPatient] = useState<SupabasePatient | null>(null);
  const [roomFilter, setRoomFilter] = useState<'all' | 'empty' | 'occupied'>('all');
  const [smplrConfig, setSmplrConfig] = useState<{
    organizationId: string;
    clientToken: string;
    spaceId: string;
  } | null>(null);

  // Fetch Smplrspace config from backend
  useEffect(() => {
    const fetchSmplrConfig = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/smplrspace/config`);
        const config = await res.json();
        console.log('🔑 Fetched Smplrspace config from backend');
        setSmplrConfig(config);
      } catch (error) {
        console.error('❌ Failed to fetch Smplrspace config:', error);
        setViewerError('Failed to load floor plan configuration');
        setUseDemoMode(true);
      }
    };
    fetchSmplrConfig();
  }, []);

  // Reset states on mount to ensure clean initialization
  useEffect(() => {
    console.log('🔄 Floor plan page mounted/remounted');
    setIsViewerReady(false);
    setRoomsLoaded(false);
    setRooms([]);
    setViewerError(null);
    setUseDemoMode(false);
    
    // Fetch rooms on mount
    fetchRoomAssignments();
  }, []);

  // Initialize Smplrspace viewer
  useEffect(() => {
    if (!containerRef.current || !smplrLoaded || !window.smplr || !smplrConfig) return;

    console.log('🎬 Initializing Smplrspace viewer...');
    let space: any = null;

    const initViewer = async () => {
      try {
        const smplr = window.smplr;

        // Use credentials from backend
        const spaceId = smplrConfig.spaceId || 'spc_demo';
        const clientToken = smplrConfig.clientToken || 'pub_demo';

        console.log('🔑 Smplrspace Config (from backend):', {
          spaceId,
          clientToken: clientToken.substring(0, 10) + '...',
          hasSpaceId: !!smplrConfig.spaceId,
          hasToken: !!smplrConfig.clientToken,
        });

        // Initialize space with credentials from backend
        space = new smplr.Space({
          spaceId,
          clientToken,
          containerId: 'smplr-container',
        });

        spaceRef.current = space;

        await space.startViewer({
          preview: false,
          mode: '3d',
          allowModeChange: true,
          onReady: async () => {
            console.log('✅ Smplrspace viewer ready');
            setIsViewerReady(true);
            setViewerError(null);
            
            // Sync rooms from Smplrspace walls
            if (smplrConfig.spaceId) {
              await syncRoomsFromSmplrspace(smplrConfig.spaceId);
              // Refetch rooms to get synced data
              await fetchRoomAssignments();
            } else {
              console.log('⚠️ Smplrspace space ID not configured');
            }
          },
          onError: (error: string) => {
            console.error('❌ Viewer error:', error);
            setViewerError(error);
            setUseDemoMode(true);
            // Rooms will be loaded from backend in the useEffect
          },
          renderOptions: {
            backgroundColor: '#fafafa',
            walls: {
              alpha: 0.8,
            },
            objects: {
              render: true,
            },
          },
          hideControls: false,
          smallControls: false,
          controlsPosition: 'bottom-right',
        });
      } catch (error) {
        console.error('❌ Failed to initialize viewer:', error);
        setViewerError('Failed to load 3D floor plan. Using simplified view.');
        setUseDemoMode(true);
      }
    };

    initViewer();

    return () => {
      console.log('🧹 Cleaning up Smplrspace viewer...');
      if (spaceRef.current) {
        try {
          spaceRef.current.remove();
          spaceRef.current = null;
        } catch (e) {
          console.error('Error removing space:', e);
        }
      }
    };
  }, [smplrLoaded, smplrConfig]);

  // Navigate camera to a specific room
  const navigateToRoom = (room: Room) => {
    if (!spaceRef.current || !isViewerReady) return;
    
    try {
      // Move camera to room position with smooth animation
      spaceRef.current.setCameraPlacement({
        alpha: -Math.PI / 4, // viewing angle in radians (45 degrees from editor position)
        beta: Math.PI / 3,   // elevation in radians (60 degrees)
        radius: 15,          // distance in meters
        target: {
          x: room.position.x,
          y: 0,
          z: room.position.z,
        },
        animate: true,
        animationDuration: 1, // duration in SECONDS (not milliseconds)
      });
      
      console.log(`📍 Navigated to ${room.name} at (${room.position.x}, ${room.position.z})`);
    } catch (error) {
      console.error('Error navigating to room:', error);
    }
  };

  // Update room markers when rooms change (patient assignment status)
  useEffect(() => {
    if (!isViewerReady || !spaceRef.current || rooms.length === 0) {
      console.log('⏸️ Skipping layer update:', { isViewerReady, hasSpace: !!spaceRef.current, roomCount: rooms.length });
      return;
    }

    console.log('🎨 Updating room visualization layers...');

    // Remove old layers if they exist
    try {
      spaceRef.current.removeDataLayer('room-icons');
      spaceRef.current.removeDataLayer('room-polygons');
      spaceRef.current.removeDataLayer('nurse-station-icons');
      spaceRef.current.removeDataLayer('nurse-station-polygons');
      console.log('🗑️ Removed old layers');
    } catch (e) {
      // Layers don't exist yet
      console.log('ℹ️ No old layers to remove');
    }

    // Add polygon highlights for PATIENT rooms (floor coloring)
    const patientPolygonData = rooms.filter(r => r.type === 'patient' && r.position.x !== 0).map(room => ({
      id: room.id + '-polygon',
      coordinates: room.position.polygon || [],
      levelIndex: room.position.levelIndex,
      room,
    }));

    if (patientPolygonData.length > 0) {
      spaceRef.current.addDataLayer({
        id: 'room-polygons',
        type: 'polygon',
        data: patientPolygonData,
        alpha: 0.4, // Subtle overlay
        color: (data: any) => {
          const room = data.room as Room;
          return room.assignedPatient ? '#10b981' : '#f3f4f6'; // Green if occupied, very light gray if empty
        },
        onClick: (data: any) => {
          const room = data.room as Room;
          setSelectedRoom(room);
        },
        tooltip: (data: any) => {
          const room = data.room as Room;
          return room.assignedPatient ? room.assignedPatient.name : room.name;
        },
      });
    }

    // Add polygon highlights for NURSE STATIONS (floor coloring)
    const nurseStationPolygonData = rooms.filter(r => r.type === 'nurse_station' && r.position.x !== 0).map(room => ({
      id: room.id + '-polygon',
      coordinates: room.position.polygon || [],
      levelIndex: room.position.levelIndex,
      room,
    }));

    if (nurseStationPolygonData.length > 0) {
      spaceRef.current.addDataLayer({
        id: 'nurse-station-polygons',
        type: 'polygon',
        data: nurseStationPolygonData,
        alpha: 0.4, // Subtle overlay
        color: '#60a5fa', // Lighter blue for nurse stations
        onClick: (data: any) => {
          const room = data.room as Room;
          setSelectedRoom(room);
        },
        tooltip: (data: any) => {
          const room = data.room as Room;
          return room.name;
        },
      });
    }

    // Add icon markers for PATIENT rooms
    const patientIconData = rooms.filter(r => r.type === 'patient' && r.position.x !== 0).map(room => ({
      id: room.id,
      position: {
        levelIndex: room.position.levelIndex,
        x: room.position.x,
        z: room.position.z,
        elevation: 1.8, // Show icon at head height
      },
      room,
    }));

    console.log(`🏥 Adding ${patientIconData.length} patient room icons`);

    if (patientIconData.length > 0) {
      spaceRef.current.addDataLayer({
        id: 'room-icons',
        type: 'icon',
        data: patientIconData,
        icon: {
          url: 'data:image/svg+xml;base64,' + btoa(`
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 20v-8a1 1 0 0 1 1-1h4V9a1 1 0 0 1 1-1h2V6a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>
              <circle cx="13" cy="9" r="1.5"/>
            </svg>
          `),
          width: 40,
          height: 40,
        },
        color: (data: any) => {
          const room = data.room as Room;
          return room.assignedPatient ? '#10b981' : '#94a3b8';
        },
        onClick: (data: any) => {
          const room = data.room as Room;
          setSelectedRoom(room);
        },
        tooltip: (data: any) => {
          const room = data.room as Room;
          return room.assignedPatient ? room.assignedPatient.name : room.name;
        },
      });
    }

    // Add icon markers for NURSE STATIONS
    const nurseStationIconData = rooms.filter(r => r.type === 'nurse_station' && r.position.x !== 0).map(room => ({
      id: room.id,
      position: {
        levelIndex: room.position.levelIndex,
        x: room.position.x,
        z: room.position.z,
        elevation: 1.8,
      },
      room,
    }));

    console.log(`👨‍⚕️ Adding ${nurseStationIconData.length} nurse station icons`);

    if (nurseStationIconData.length > 0) {
      spaceRef.current.addDataLayer({
        id: 'nurse-station-icons',
        type: 'icon',
        data: nurseStationIconData,
        icon: {
          url: 'data:image/svg+xml;base64,' + btoa(`
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM4 18c0-3.31 6.71-5 8-5s8 1.69 8 5v4H4v-4z"/>
            </svg>
          `),
          width: 40,
          height: 40,
        },
        color: '#3b82f6',
        onClick: (data: any) => {
          const room = data.room as Room;
          setSelectedRoom(room);
        },
        tooltip: (data: any) => {
          const room = data.room as Room;
          return room.name;
        },
      });
    }

    console.log('✅ Room visualization layers updated successfully!');
  }, [isViewerReady, rooms]);

  // Sync rooms from Smplrspace using automatic room detection
  const syncRoomsFromSmplrspace = async (spaceId: string) => {
    try {
      // Use smplr.js QueryClient to get automatic rooms from walls
      if (!window.smplr) {
        console.error('❌ Smplr.js not loaded');
        return;
      }

      if (!smplrConfig) {
        console.error('❌ Smplrspace config not loaded from backend');
        return;
      }

      const smplrClient = new window.smplr.QueryClient({
        organizationId: smplrConfig.organizationId,
        clientToken: smplrConfig.clientToken,
      });

      console.log('🔄 Detecting rooms from walls using Smplrspace API...');

      // First, get ALL rooms from walls
      const allRoomsData = await smplrClient.getRoomsOnLevel({
        spaceId: spaceId,
        levelIndex: 0,
        useCache: false,
      });

      console.log('🏠 All rooms detected from walls:', allRoomsData);

      if (!allRoomsData || allRoomsData.length === 0) {
        console.log('⚠️ No rooms detected from walls. Your floor plan may not have fully enclosed rooms.');
        return;
      }

      console.log(`✅ Detected ${allRoomsData.length} rooms from wall geometry`);

      // Get space definition to access annotations
      const space = spaceRef.current;
      if (!space) {
        console.error('❌ Space not initialized');
        return;
      }

      const definition = space.getDefinition();
      
      // Annotations are nested inside levels[0].annotations
      const level0 = definition?.levels?.[0];
      const annotationsArray = level0?.annotations || [];
      
      console.log('📋 All annotations:', annotationsArray);
      
      // Get all room and nurse station annotations (exclude "Entrance")
      const hospitalAnnotations = annotationsArray.filter((a: any) => {
        const name = a.name || a.text || '';
        const nameLower = name.toLowerCase();
        // Match "Room X" pattern, "Hospital Room", or "Nurse Station"
        return (
          nameLower.startsWith('room ') || 
          nameLower.includes('hospital room') ||
          nameLower.includes('nurse station')
        ) && !nameLower.includes('entrance');
      });

      console.log(`🏥 Found ${hospitalAnnotations.length} room/station annotations:`, hospitalAnnotations.map(a => a.name));

      // Match hospital annotations to detected rooms
      const rooms: any[] = [];
      const usedRoomIndices = new Set(); // Track which rooms we've already used
      
      if (hospitalAnnotations.length > 0) {
        // Match each annotation to the nearest unused room
        for (let i = 0; i < hospitalAnnotations.length; i++) {
          const annotation = hospitalAnnotations[i];
          const annotX = annotation.r || 0;
          const annotZ = annotation.t || 0;
          
          console.log(`📍 Finding room for "${annotation.name}" at (${annotX}, ${annotZ})`);
          
          // Find the closest room to this annotation
          let closestRoomIndex = -1;
          let closestDistance = Infinity;
          
          for (let j = 0; j < allRoomsData.length; j++) {
            if (usedRoomIndices.has(j)) continue; // Skip already used rooms
            
            const roomData = allRoomsData[j];
            if (roomData.room && roomData.room.length > 0) {
              // Calculate center point of room polygon
              const centerX = roomData.room.reduce((sum: number, p: any) => sum + p.x, 0) / roomData.room.length;
              const centerZ = roomData.room.reduce((sum: number, p: any) => sum + p.z, 0) / roomData.room.length;
              
              // Calculate distance from annotation to room center
              const distance = Math.sqrt(
                Math.pow(annotX - centerX, 2) + Math.pow(annotZ - centerZ, 2)
              );
              
              if (distance < closestDistance) {
                closestDistance = distance;
                closestRoomIndex = j;
              }
            }
          }
          
          // Use the closest room
          if (closestRoomIndex >= 0) {
            const roomData = allRoomsData[closestRoomIndex];
            const centerX = roomData.room.reduce((sum: number, p: any) => sum + p.x, 0) / roomData.room.length;
            const centerZ = roomData.room.reduce((sum: number, p: any) => sum + p.z, 0) / roomData.room.length;
            
            // Determine room type based on annotation name
            const nameLower = (annotation.name || '').toLowerCase();
            const room_type = nameLower.includes('nurse station') ? 'nurse_station' : 'patient';
            
            rooms.push({
              id: annotation.id || `room-${i + 1}`,
              name: annotation.name || `Room ${i + 1}`,
              room_type: room_type, // Add room_type
              levelIndex: 0,
              position: { x: centerX, z: centerZ },
              polygon: roomData.room,
              holes: roomData.holes || [],
            });
            
            usedRoomIndices.add(closestRoomIndex);
            console.log(`✅ Matched "${annotation.name}" (type: ${room_type}) to room at (${centerX.toFixed(2)}, ${centerZ.toFixed(2)}) - distance: ${closestDistance.toFixed(2)}m`);
          } else {
            console.warn(`⚠️ Could not find room for "${annotation.name}"`);
          }
        }
      } else {
        // No hospital annotations - use all detected rooms
        console.log('📦 No "Hospital Room" annotations found, using all detected rooms');
        for (let i = 0; i < allRoomsData.length; i++) {
          const roomData = allRoomsData[i];
          if (roomData.room && roomData.room.length > 0) {
            const centerX = roomData.room.reduce((sum: number, p: any) => sum + p.x, 0) / roomData.room.length;
            const centerZ = roomData.room.reduce((sum: number, p: any) => sum + p.z, 0) / roomData.room.length;

            rooms.push({
              id: `auto-room-${i + 1}`,
              name: `Room ${i + 1}`,
              room_type: 'patient', // Default to patient for auto-detected rooms
              levelIndex: 0,
              position: { x: centerX, z: centerZ },
              polygon: roomData.room,
              holes: roomData.holes || [],
            });
          }
        }
      }

      if (rooms.length === 0) {
        console.log('⚠️ Could not match any rooms');
        return;
      }

      console.log(`✅ Prepared ${rooms.length} rooms for sync`);

      // Sync to backend with floor_id
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms/sync-from-smplrspace`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          rooms,
          floor_id: 'floor-1' // Default floor
        }),
      });

      const result = await res.json();
      
      if (result.error) {
        console.error('❌ Error syncing rooms:', result.error);
        return;
      }

      console.log(`✅ Synced ${result.synced_count} rooms from Smplrspace walls`);
    } catch (error) {
      console.error('❌ Error syncing rooms from Smplrspace:', error);
    }
  };

  // Fetch room assignments from backend
  const fetchRoomAssignments = async () => {
    try {
      console.log('🔄 Fetching rooms from backend...');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms`);
      const assignments = await res.json();
      
      console.log('📦 Backend response:', assignments);
      
      if (Array.isArray(assignments) && assignments.length > 0) {
        console.log(`✅ Loaded ${assignments.length} room assignments from backend`);
        
        // Log first assignment's metadata to debug position extraction
        if (assignments[0]) {
          console.log('🔍 First room metadata:', assignments[0].metadata);
          console.log('🔍 Smplrspace data:', assignments[0].metadata?.smplrspace_data);
          console.log('🔍 Position:', assignments[0].metadata?.smplrspace_data?.position);
        }
        
        // Convert backend room assignments to frontend Room format
        const backendRooms: Room[] = assignments.map((assignment: any) => {
          const metadata = assignment.metadata || {};
          const smplrData = metadata.smplrspace_data || {};
          
          const position = {
            levelIndex: 0,
            x: smplrData.position?.x || 0,
            z: smplrData.position?.z || 0,
            polygon: metadata.polygon || [],
          };
          
          console.log(`📍 Room "${assignment.room_name}" position:`, {
            x: position.x,
            z: position.z,
            polygonPoints: position.polygon.length
          });
          
          return {
          id: assignment.room_id,
          name: assignment.room_name,
          type: assignment.room_type,
            position,
          assignedPatient: assignment.patient_id ? {
            patient_id: assignment.patient_id,
            name: assignment.patient_name || 'Unknown',
            age: 0,
            condition: '',
            photo_url: '',
          } : undefined,
          };
        });
        
        console.log('🏠 Frontend rooms with positions:', backendRooms.map(r => ({
          name: r.name,
          x: r.position.x,
          z: r.position.z
        })));
        setRooms(backendRooms);
        setRoomsLoaded(true);
      } else {
        console.log('⚠️ No rooms found in backend (empty array or non-array response)');
        console.log('Response type:', typeof assignments, 'Value:', assignments);
        setRoomsLoaded(true);
      }
    } catch (error) {
      console.error('❌ Error fetching room assignments:', error);
      setRoomsLoaded(true);
    }
  };

  // Fetch room assignments from backend on page load
  useEffect(() => {
    fetchRoomAssignments();
  }, []);

  // Fetch available patients
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients/search?q=`);
        const data = await res.json();
        setAvailablePatients(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching patients:', error);
      }
    };

    fetchPatients();
  }, []);

  const assignPatientToRoom = async (patient: SupabasePatient, roomId?: string) => {
    const targetRoomId = roomId || selectedRoom?.id;
    if (!targetRoomId) return;

    try {
      // Call backend API to persist assignment
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms/assign-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_id: targetRoomId,
          patient_id: patient.patient_id,
        }),
      });

      const result = await res.json();

      if (result.error) {
        console.error('❌ Error assigning patient:', result.error);
        alert(`Error: ${result.error}`);
        return;
      }

      console.log('✅ Patient assigned to room:', result);

      // Update local state
      const updatedRooms = rooms.map(room => {
        if (room.id === targetRoomId) {
          return {
            ...room,
            assignedPatient: {
              patient_id: patient.patient_id,
              name: patient.name,
              age: patient.age,
              condition: patient.condition,
              photo_url: patient.photo_url,
            },
          };
        }
        return room;
      });
      setRooms(updatedRooms);
      
      // Update selected room to show new assignment
      if (selectedRoom && selectedRoom.id === targetRoomId) {
        setSelectedRoom(updatedRooms.find(r => r.id === targetRoomId) || null);
      }
    } catch (error) {
      console.error('❌ Error assigning patient:', error);
      alert('Failed to assign patient. Please try again.');
    }
  };

  const unassignPatient = async (roomId: string) => {
    try {
      // Call backend API to remove assignment
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms/unassign-patient/${roomId}`, {
        method: 'DELETE',
      });

      const result = await res.json();

      if (result.error) {
        console.error('❌ Error unassigning patient:', result.error);
        alert(`Error: ${result.error}`);
        return;
      }

      console.log('✅ Patient unassigned from room:', result);

      // Update local state
      setRooms(prev => prev.map(room => {
        if (room.id === roomId) {
          const { assignedPatient, ...rest } = room;
          return rest;
        }
        return room;
      }));
    } catch (error) {
      console.error('❌ Error unassigning patient:', error);
      alert('Failed to unassign patient. Please try again.');
    }
  };

  // Drag and drop handlers
  const handleDragStart = (patient: SupabasePatient) => {
    setDraggedPatient(patient);
  };

  const handleDragEnd = () => {
    setDraggedPatient(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault(); // Allow drop
  };

  const handleDrop = async (e: React.DragEvent, room: Room) => {
    e.preventDefault();
    if (draggedPatient && !room.assignedPatient) {
      await assignPatientToRoom(draggedPatient, room.id);
      setDraggedPatient(null);
    }
  };

  const assignedPatientIds = rooms
    .filter(r => r.assignedPatient)
    .map(r => r.assignedPatient!.patient_id);

  const filteredPatients = availablePatients.filter(
    p => !assignedPatientIds.includes(p.patient_id)
  );

  // Filter and sort all rooms (patient rooms and nurse stations)
  const getFilteredAndSortedRooms = () => {
    let allRooms = [...rooms];
    
    // Apply filter (only for patient rooms, nurse stations always show if filter is 'all')
    if (roomFilter === 'empty') {
      allRooms = allRooms.filter(r => r.type === 'patient' && !r.assignedPatient);
    } else if (roomFilter === 'occupied') {
      allRooms = allRooms.filter(r => r.type === 'patient' && r.assignedPatient);
    }
    // 'all' shows everything
    
    // Sort: patient rooms first (empty, then occupied), then nurse stations
    return allRooms.sort((a, b) => {
      // Nurse stations always go to the end
      if (a.type === 'nurse_station' && b.type !== 'nurse_station') return 1;
      if (a.type !== 'nurse_station' && b.type === 'nurse_station') return -1;
      
      // For patient rooms, sort by occupied status (empty first)
      if (a.type === 'patient' && b.type === 'patient') {
        const aOccupied = a.assignedPatient ? 1 : 0;
        const bOccupied = b.assignedPatient ? 1 : 0;
        return aOccupied - bOccupied;
      }
      
      return 0;
    });
  };

  const filteredAndSortedRooms = getFilteredAndSortedRooms();

  return (
    <div className="h-full">
      {/* Load Smplrspace library */}
      <Script
        src="https://app.smplrspace.com/lib/smplr.js"
        strategy="afterInteractive"
        onLoad={() => {
          console.log('✅ Smplr.js loaded');
          setSmplrLoaded(true);
        }}
        onError={(e) => {
          console.error('❌ Failed to load Smplr.js:', e);
          setViewerError('Failed to load 3D viewer library');
          setUseDemoMode(true);
          // Rooms will be loaded from backend in the useEffect
        }}
      />
      <link href="https://app.smplrspace.com/lib/smplr.css" rel="stylesheet" />
      
      {/* Main Content */}
      <div className="grid grid-cols-12 gap-6 p-6 h-[calc(100vh-4rem)]">
        {/* Floor Plan Viewer (Left - 8 columns) */}
        <div className="col-span-8 flex flex-col">
          <div className="bg-surface border border-neutral-200 flex-1 flex flex-col">
            <div className="px-5 py-4 border-b border-neutral-200">
              <p className="text-sm font-light text-neutral-600">
                Hospital View
              </p>
            </div>

            <div className="p-6 flex-1 flex flex-col">

            {/* Error Message */}
            {viewerError && (
              <div className="bg-yellow-50 border border-yellow-200 p-3 mb-4">
                <p className="text-xs font-light text-neutral-600">
                  {viewerError}
                </p>
              </div>
            )}

            {/* Smplrspace Container or Demo Grid */}
            {useDemoMode ? (
              // Demo Mode: Simple 2D Grid
              <div className="w-full flex-1 bg-neutral-50 p-6">
                <div className="grid grid-cols-3 gap-4 h-full">
                  {rooms.filter(r => r.type === 'patient').map((room: Room) => (
                    <button
                      key={room.id}
                      onClick={() => {
                        setSelectedRoom(room);
                      }}
                      className={`border p-4 transition-all ${
                        room.assignedPatient
                          ? 'bg-primary-50 border-primary-700'
                          : 'bg-surface border-neutral-200 hover:border-primary-700'
                      } ${selectedRoom?.id === room.id ? 'ring-1 ring-primary-700' : ''}`}
                    >
                      <div className="text-center">
                        <div className={`w-12 h-12 mx-auto mb-2 border flex items-center justify-center ${
                          room.assignedPatient
                            ? 'bg-primary-700 border-primary-700'
                            : 'bg-neutral-100 border-neutral-200'
                        }`}>
                          {room.assignedPatient ? (
                            <img
                              src={room.assignedPatient.photo_url}
                              alt={room.assignedPatient.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <span className="text-xl text-neutral-400">+</span>
                          )}
                        </div>
                        <p className="text-xs font-light text-neutral-600 mb-1">{room.name}</p>
                        {room.assignedPatient ? (
                          <div>
                            <p className="text-xs font-light text-neutral-950 truncate">
                              {room.assignedPatient.name}
                            </p>
                            <p className="text-[10px] text-primary-700">
                              {room.assignedPatient.patient_id}
                            </p>
                          </div>
                        ) : (
                          <p className="text-[10px] text-neutral-400">Empty</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              // 3D Smplrspace Viewer
              <div
                id="smplr-container"
                ref={containerRef}
                className="w-full flex-1 bg-neutral-50 relative z-0"
              />
            )}
          </div>
          </div>
        </div>

        {/* Right Panel - Legend & Room List (4 columns) */}
        <div className="col-span-4 flex flex-col space-y-4 overflow-hidden">
          {selectedRoom ? (
            <RoomDetailsPanel
              room={selectedRoom}
              onClose={() => setSelectedRoom(null)}
              onUnassignPatient={() => {
                if (selectedRoom) {
                  unassignPatient(selectedRoom.id);
                  setSelectedRoom(null);
                }
              }}
              availablePatients={filteredPatients}
              onAssignPatient={(patient) => assignPatientToRoom(patient, selectedRoom.id)}
            />
          ) : (
            <>
              {/* Legend - Always Visible */}
              <div className="bg-surface border-b border-neutral-200 px-5 py-4">
                <FloorPlanLegend
                  totalRooms={rooms.filter(r => r.type === 'patient').length}
                  occupiedRooms={rooms.filter(r => r.assignedPatient).length}
                  totalNurses={rooms.reduce((sum, r) => sum + (r.assignedNurses?.length || 0), 0)}
                  nurseStations={rooms.filter(r => r.type === 'nurse_station').length}
                />
              </div>

              {/* Available Patients - Collapsible */}
              <div className="bg-surface flex-shrink-0">
                <button
                  onClick={() => setPatientsListCollapsed(!patientsListCollapsed)}
                  className="w-full px-5 py-4 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-light text-neutral-600">Available Patients</p>
                    <span className="text-xs font-light text-primary-700 bg-primary-100 px-2 py-0.5 rounded">
                      {filteredPatients.length}
                    </span>
                  </div>
                  <svg 
                    className={`w-5 h-5 text-neutral-400 transition-transform ${patientsListCollapsed ? '' : 'rotate-180'}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>

                {!patientsListCollapsed && (
                  <div className="overflow-y-auto max-h-[350px]">
                    {filteredPatients.length === 0 ? (
                      <div className="p-5 text-center">
                        <p className="text-sm font-light text-neutral-400">
                          No available patients
                        </p>
                      </div>
                    ) : (
                      filteredPatients.map((patient) => (
                        <div
                          key={patient.id}
                          draggable
                          onDragStart={() => handleDragStart(patient)}
                          onDragEnd={handleDragEnd}
                          className={`border-b border-neutral-200 p-4 cursor-move hover:bg-neutral-50 transition-colors ${
                            draggedPatient?.id === patient.id ? 'opacity-50' : ''
                          }`}
                        >
                      <div className="flex items-center gap-3">
                            <svg className="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                            </svg>
                            {patient.photo_url ? (
                              <img
                                src={patient.photo_url}
                                alt={patient.name}
                                className="w-10 h-10 object-cover border border-neutral-300 flex-shrink-0"
                              />
                            ) : (
                              <div className="w-10 h-10 border border-neutral-300 bg-primary-100 flex items-center justify-center flex-shrink-0">
                                <span className="text-sm font-light text-primary-700">
                                  {patient.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                      </span>
                    </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="font-light text-neutral-950 text-sm truncate">{patient.name}</p>
                              <p className="text-xs font-light text-neutral-500">
                                {patient.age}y/o • {patient.patient_id}
                              </p>
                  </div>
              </div>
            </div>
                      ))
          )}
        </div>
                )}
              </div>

              {/* All Rooms - Collapsible */}
              <div className="bg-surface flex-1 flex flex-col overflow-hidden">
                <button
                  onClick={() => setRoomsListCollapsed(!roomsListCollapsed)}
                  className="w-full px-5 py-4 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition-colors flex-shrink-0"
                >
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-light text-neutral-600">All Rooms</p>
                    <span className="text-xs font-light text-neutral-400">
                      {filteredAndSortedRooms.length}
                    </span>
                  </div>
                  <svg 
                    className={`w-5 h-5 text-neutral-400 transition-transform ${roomsListCollapsed ? '' : 'rotate-180'}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>

                {!roomsListCollapsed && (
                  <>
                    {/* Filter Controls */}
                    <div className="px-5 py-3 border-b border-neutral-200 flex gap-4 flex-shrink-0">
                <button
                        onClick={() => setRoomFilter('all')}
                        className={`px-3 py-1.5 text-xs font-light transition-colors ${
                          roomFilter === 'all'
                            ? 'text-neutral-950 border-b-2 border-primary-700'
                            : 'text-neutral-500 hover:text-neutral-950'
                        }`}
                      >
                        All
                      </button>
                      <button
                        onClick={() => setRoomFilter('empty')}
                        className={`px-3 py-1.5 text-xs font-light transition-colors ${
                          roomFilter === 'empty'
                            ? 'text-neutral-950 border-b-2 border-primary-700'
                            : 'text-neutral-500 hover:text-neutral-950'
                        }`}
                      >
                        Empty
                      </button>
                      <button
                        onClick={() => setRoomFilter('occupied')}
                        className={`px-3 py-1.5 text-xs font-light transition-colors ${
                          roomFilter === 'occupied'
                            ? 'text-neutral-950 border-b-2 border-primary-700'
                            : 'text-neutral-500 hover:text-neutral-950'
                        }`}
                      >
                        Occupied
                      </button>
                    </div>

                    <div className="overflow-y-auto flex-1">
                      {filteredAndSortedRooms.map((room: Room) => {
                        // Handle both patient rooms and nurse stations
                        if (room.type === 'nurse_station') {
                          const nurseCount = room.assignedNurses?.length || 0;
                          return (
                  <div
                    key={room.id}
                    className={`border-b border-neutral-200 p-4 hover:bg-neutral-50 transition-colors cursor-pointer ${
                                selectedRoom?.id === room.id ? 'bg-primary-50' : ''
                    }`}
                    onClick={() => {
                      setSelectedRoom(room);
                                navigateToRoom(room);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                                  <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                          <p className="font-light text-neutral-950 text-sm">{room.name}</p>
                                      <span className="text-[10px] font-light text-neutral-500 uppercase tracking-wider">
                                        Station
                      </span>
                    </div>
                  </div>
              </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-light text-neutral-400">
                                    {nurseCount} Staff
                                  </span>
                                  <svg className="w-4 h-4 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
            </div>
        </div>
      </div>
                          );
                        } else {
                          // Patient room
                          const statusColor = room.assignedPatient ? 'bg-primary-700' : 'bg-neutral-300';
                          const statusText = room.assignedPatient ? 'Occupied' : 'Empty';
                          const canDrop = !room.assignedPatient && draggedPatient !== null;
                          
                          return (
                            <div
                              key={room.id}
                              className={`border-b border-neutral-200 p-4 transition-colors cursor-pointer ${
                                selectedRoom?.id === room.id ? 'bg-primary-50' : ''
                              } ${canDrop ? 'hover:bg-green-50 hover:border-green-300' : 'hover:bg-neutral-50'}`}
                              onClick={() => {
                                setSelectedRoom(room);
                                navigateToRoom(room);
                              }}
                              onDragOver={canDrop ? handleDragOver : undefined}
                              onDrop={canDrop ? (e) => handleDrop(e, room) : undefined}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className={`w-2.5 h-2.5 rounded-full ${statusColor}`} />
                                  <div className="flex-1 min-w-0">
                                    <p className="font-light text-neutral-950 text-sm">{room.name}</p>
                                    {room.assignedPatient && (
                                      <p className="text-xs font-light text-neutral-500 mt-1 truncate">
                                        {room.assignedPatient.name}
                                      </p>
                                    )}
                                  </div>
                                </div>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  <span className="text-xs font-light text-neutral-400">
                                    {statusText}
                                  </span>
                                  <svg className="w-4 h-4 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                </div>
                              </div>
                            </div>
                          );
                        }
                      })}
                    </div>
                  </>
              )}
            </div>
            </>
          )}
          </div>
        </div>

      {/* Nurse Assignment Modal */}
      {showNurseModal && selectedRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-neutral-950/40"
            onClick={() => {
              setShowNurseModal(false);
              setSelectedRoom(null);
            }}
          />

          <div className="relative bg-surface border border-neutral-200 max-w-md w-full shadow-lg">
            <div className="p-4 border-b border-neutral-200">
              <h2 className="text-base font-light text-neutral-950">
                Manage {selectedRoom.name}
              </h2>
            </div>

            <div className="p-4">
              <p className="text-xs font-light text-neutral-500 mb-3">
                Nurse station management coming soon
              </p>
              <button
                onClick={() => {
                  setShowNurseModal(false);
                  setSelectedRoom(null);
                }}
                className="w-full border border-neutral-200 px-4 py-2 text-xs font-light hover:bg-neutral-50 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

