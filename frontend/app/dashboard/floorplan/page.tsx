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
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [showNurseModal, setShowNurseModal] = useState(false);
  const [availablePatients, setAvailablePatients] = useState<SupabasePatient[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roomsLoaded, setRoomsLoaded] = useState(false);
  const [legendCollapsed, setLegendCollapsed] = useState(false);
  const [roomsListCollapsed, setRoomsListCollapsed] = useState(false);
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

  // Update furniture colors when rooms change (patient assignment status)
  useEffect(() => {
    if (!isViewerReady || !spaceRef.current || rooms.length === 0) return;

    // Use furniture layer to color actual furniture/equipment in the floor plan
    const furnitureData = rooms.map(room => ({
      id: room.id,
      furnitureId: room.id,
      room,
    }));

    // Remove old layer if exists
    try {
      spaceRef.current.removeDataLayer('room-status');
    } catch (e) {
      // Layer doesn't exist yet
    }

    // Add furniture layer with room status colors
    if (furnitureData.length > 0) {
      spaceRef.current.addDataLayer({
        id: 'room-status',
        type: 'furniture',
        data: furnitureData,
        color: (data: any) => {
          const room = data.room as Room;
          if (room.type === 'nurse_station') {
            return '#c97064'; // Terracotta for nurse stations
          }
          return room.assignedPatient ? '#6b9080' : '#cbd5e1'; // Green if occupied, gray if empty
        },
        onClick: (data: any) => {
          const room = data.room as Room;
          setSelectedRoom(room);
          if (room.type === 'nurse_station') {
            setShowNurseModal(true);
          } else {
            if (!room.assignedPatient) {
              setShowPatientModal(true);
            }
          }
        },
        tooltip: (data: any) => {
          const room = data.room as Room;
          
          if (room.type === 'nurse_station') {
            const nurseCount = room.assignedNurses?.length || 0;
            return `
              <div style="min-width: 200px; padding: 4px;">
                <div style="font-weight: 500; font-size: 14px; margin-bottom: 8px; color: #0f172a;">
                  ${room.name}
                </div>
                <div style="font-size: 12px; color: #475569;">
                  <strong>Nurses on duty:</strong> ${nurseCount}
                </div>
              </div>
            `;
          }
          
          if (room.assignedPatient) {
            return `
              <div style="min-width: 220px; padding: 4px;">
                <div style="font-weight: 500; font-size: 14px; margin-bottom: 8px; color: #0f172a;">
                  ${room.name}
                </div>
                <div style="font-size: 12px; color: #475569; margin-bottom: 4px;">
                  <strong>Patient:</strong> ${room.assignedPatient.name}
                </div>
                <div style="font-size: 12px; color: #475569; margin-bottom: 4px;">
                  <strong>ID:</strong> ${room.assignedPatient.patient_id}
                </div>
                <div style="font-size: 11px; color: #94a3b8;">
                  ${room.assignedPatient.age}y/o • ${room.assignedPatient.condition}
                </div>
              </div>
            `;
          }
          
          return `
            <div style="min-width: 150px; padding: 4px;">
              <div style="font-weight: 500; font-size: 14px; color: #0f172a;">
                ${room.name}
              </div>
              <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                Empty - Click to assign patient
              </div>
            </div>
          `;
        },
      });
    }
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

      // Get space definition to access annotations
      const space = spaceRef.current;
      if (!space) {
        console.error('❌ Space not initialized');
        return;
      }

      const definition = space.getDefinition();
      console.log('📐 Space definition:', definition);
      
      // Get all annotations labeled "Hospital Room"
      let hospitalAnnotations = definition?.annotations?.filter((a: any) => 
        a.text?.toLowerCase().includes('hospital room')
      ) || [];

      console.log('📋 All annotations:', definition?.annotations);
      console.log('🏥 Hospital Room annotations:', hospitalAnnotations);

      // Fallback: if no "Hospital Room" annotations found, try furniture
      if (hospitalAnnotations.length === 0) {
        console.log('⚠️ No annotations labeled "Hospital Room" found');
        console.log('💡 TIP: In Smplrspace editor, add text annotations labeled "Hospital Room" to mark patient rooms');
        console.log('📦 Trying furniture as fallback...');
        
        hospitalAnnotations = definition?.furniture?.filter((f: any) => 
          f.name?.toLowerCase().includes('hospital room')
        ) || [];
        
        if (hospitalAnnotations.length === 0) {
          console.log('❌ No "Hospital Room" annotations or furniture found');
          console.log('💡 Add text annotations in Smplrspace editor: Right-click → Add annotation → "Hospital Room"');
          return;
        }
        
        console.log(`📦 Found ${hospitalAnnotations.length} furniture items as fallback`);
      } else {
        console.log(`🏥 Found ${hospitalAnnotations.length} Hospital Room annotations`);
      }

      // For each hospital room annotation/marker, find which room it's in
      const rooms: any[] = [];
      for (let i = 0; i < hospitalAnnotations.length; i++) {
        const annotation = hospitalAnnotations[i];
        
        try {
          // Get the room at this annotation's position
          const roomData = await smplrClient.getRoomAtPoint({
            spaceId: spaceId,
            point: {
              levelIndex: annotation.levelIndex || 0,
              x: annotation.position?.x || annotation.x || 0,
              z: annotation.position?.z || annotation.z || 0,
            },
          });

          console.log(`📍 Checking annotation "${annotation.text || annotation.name}" at position:`, {
            levelIndex: annotation.levelIndex,
            x: annotation.position?.x || annotation.x,
            z: annotation.position?.z || annotation.z,
            roomFound: !!roomData
          });

          if (roomData && roomData.room) {
            // Calculate center point of room polygon
            const centerX = roomData.room.reduce((sum: number, p: any) => sum + p.x, 0) / roomData.room.length;
            const centerZ = roomData.room.reduce((sum: number, p: any) => sum + p.z, 0) / roomData.room.length;

            rooms.push({
              id: annotation.id || `room-${i + 1}`,
              name: annotation.text || annotation.name || `Room ${i + 1}`,
              levelIndex: annotation.levelIndex || 0,
              position: { x: centerX, z: centerZ },
              polygon: roomData.room,
              holes: roomData.holes || [],
            });
          }
        } catch (error) {
          console.warn(`⚠️ Could not find room for annotation: ${annotation.text || annotation.name}`, error);
        }
      }

      if (rooms.length === 0) {
        console.log('⚠️ No rooms found for Hospital Room markers');
        return;
      }

      console.log(`✅ Detected ${rooms.length} hospital rooms`);

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
        console.log('📋 Room details:', assignments.map(a => ({
          id: a.room_id,
          name: a.room_name,
          type: a.room_type,
          patient: a.patient_id ? a.patient_name : 'Empty'
        })));
        
        // Convert backend room assignments to frontend Room format
        const backendRooms: Room[] = assignments.map((assignment: any) => ({
          id: assignment.room_id,
          name: assignment.room_name,
          type: assignment.room_type,
          position: {
            levelIndex: assignment.floor_id ? 0 : 0, // Use floor_id
            x: assignment.metadata?.smplrspace_data?.position?.x || 0,
            z: assignment.metadata?.smplrspace_data?.position?.z || 0,
          },
          assignedPatient: assignment.patient_id ? {
            patient_id: assignment.patient_id,
            name: assignment.patient_name || 'Unknown',
            age: 0,
            condition: '',
            photo_url: '',
          } : undefined,
        }));
        
        console.log('🏠 Frontend rooms:', backendRooms);
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
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients/search?q=${searchQuery}`);
        const data = await res.json();
        setAvailablePatients(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching patients:', error);
      }
    };

    const timeout = setTimeout(fetchPatients, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  const assignPatientToRoom = async (patient: SupabasePatient) => {
    if (!selectedRoom) return;

    try {
      // Call backend API to persist assignment
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms/assign-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_id: selectedRoom.id,
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
      setRooms(prev => prev.map(room => {
        if (room.id === selectedRoom.id) {
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
      }));

      setShowPatientModal(false);
      setSelectedRoom(null);
      setSearchQuery('');
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

  const assignedPatientIds = rooms
    .filter(r => r.assignedPatient)
    .map(r => r.assignedPatient!.patient_id);

  const filteredPatients = availablePatients.filter(
    p => !assignedPatientIds.includes(p.patient_id)
  );

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
      <div className="grid grid-cols-12 gap-4 p-4">
        {/* Floor Plan Viewer (Left - 8 columns) */}
        <div className="col-span-8 space-y-4">
          <div className="bg-surface border border-neutral-200">
            <div className="px-4 py-3 border-b border-neutral-200">
              <p className="text-xs font-light text-neutral-500">
                {useDemoMode ? '2D Floor Plan View' : '3D Floor Plan View'}
              </p>
            </div>

            <div className="p-4">

            {/* Error Message */}
            {viewerError && (
              <div className="bg-yellow-50 border border-yellow-200 p-2 mb-3">
                <p className="text-[10px] font-light text-neutral-600">
                  {viewerError}
                </p>
              </div>
            )}

            {/* Smplrspace Container or Demo Grid */}
            {useDemoMode ? (
              // Demo Mode: Simple 2D Grid
              <div className="w-full h-[600px] bg-neutral-50 p-6">
                <div className="grid grid-cols-3 gap-4 h-full">
                  {rooms.filter(r => r.type === 'patient').map((room: Room) => (
                    <button
                      key={room.id}
                      onClick={() => {
                        setSelectedRoom(room);
                        if (!room.assignedPatient) {
                          setShowPatientModal(true);
                        }
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
                className="w-full h-[600px] bg-neutral-50"
                style={{ position: 'relative' }}
              />
            )}
            </div>
          </div>
        </div>

        {/* Right Panel - Legend & Room List (4 columns) */}
        <div className="col-span-4 space-y-4">
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
              onAssignClick={() => {
                setShowPatientModal(true);
              }}
            />
          ) : (
            <>
              {/* Legend - Collapsible */}
              <div className="bg-surface border border-neutral-200">
                <button
                  onClick={() => setLegendCollapsed(!legendCollapsed)}
                  className="w-full px-4 py-3 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                >
                  <p className="text-xs font-light text-neutral-500">Legend</p>
                  <svg 
                    className={`w-4 h-4 text-neutral-400 transition-transform ${legendCollapsed ? '' : 'rotate-180'}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>

                {!legendCollapsed && (
                  <div className="px-4 py-3">
                    <FloorPlanLegend
                      totalRooms={rooms.filter(r => r.type === 'patient').length}
                      occupiedRooms={rooms.filter(r => r.assignedPatient).length}
                      totalNurses={rooms.reduce((sum, r) => sum + (r.assignedNurses?.length || 0), 0)}
                    />
                  </div>
                )}
              </div>

              {/* All Rooms - Collapsible */}
              <div className="bg-surface border border-neutral-200">
                <button
                  onClick={() => setRoomsListCollapsed(!roomsListCollapsed)}
                  className="w-full px-4 py-3 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                >
                  <p className="text-xs font-light text-neutral-500">All Rooms</p>
                  <svg 
                    className={`w-4 h-4 text-neutral-400 transition-transform ${roomsListCollapsed ? '' : 'rotate-180'}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>

                {!roomsListCollapsed && (
                  <div className="overflow-y-auto max-h-[calc(100vh-400px)]">
                {rooms.filter(r => r.type === 'patient').map((room: Room) => (
                  <div
                    key={room.id}
                    className={`border-b border-neutral-200 p-3 hover:bg-neutral-50 transition-colors cursor-pointer ${
                      selectedRoom?.id === room.id ? 'bg-primary-50' : ''
                    }`}
                    onClick={() => {
                      setSelectedRoom(room);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${
                          room.assignedPatient ? 'bg-primary-700' : 'bg-neutral-300'
                        }`} />
                        <div>
                          <p className="font-light text-neutral-950 text-xs">{room.name}</p>
                          {room.assignedPatient && (
                            <p className="text-[10px] font-light text-neutral-500 mt-0.5">
                              {room.assignedPatient.name}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-[10px] font-light text-neutral-400">
                        {room.assignedPatient ? 'Occupied' : 'Empty'}
                      </span>
                    </div>
                  </div>
                ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Patient Assignment Modal */}
      {showPatientModal && selectedRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-neutral-950/40"
            onClick={() => {
              setShowPatientModal(false);
              setSelectedRoom(null);
              setSearchQuery('');
            }}
          />

          <div className="relative bg-surface border border-neutral-200 max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-lg">
            {/* Header */}
            <div className="p-4 border-b border-neutral-200">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-light text-neutral-950">
                  Assign Patient to {selectedRoom.name}
                </h2>
                <button
                  onClick={() => {
                    setShowPatientModal(false);
                    setSelectedRoom(null);
                    setSearchQuery('');
                  }}
                  className="text-neutral-500 hover:text-neutral-950 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Search */}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patients by name..."
                className="w-full bg-white border border-neutral-200 px-4 py-3 font-light text-sm text-neutral-950 placeholder:text-neutral-400 focus:outline-none focus:border-primary-700 transition-all"
                autoFocus
              />
            </div>

            {/* Patient List */}
            <div className="p-4 overflow-y-auto max-h-[calc(80vh-180px)]">
              {filteredPatients.length === 0 ? (
                <div className="text-center py-12 border border-neutral-200 bg-neutral-50">
                  <p className="text-neutral-500 text-sm font-light">
                    {searchQuery ? 'No patients found' : 'Start typing to search patients'}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {filteredPatients.map((patient) => (
                    <button
                      key={patient.id}
                      onClick={() => assignPatientToRoom(patient)}
                      className="flex items-start gap-3 p-3 bg-surface hover:bg-neutral-50 border border-neutral-200 hover:border-primary-700 transition-all text-left"
                    >
                      <img
                        src={patient.photo_url}
                        alt={patient.name}
                        className="w-12 h-12 object-cover border border-neutral-300"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <h3 className="font-light text-neutral-950 text-sm">
                            {patient.name}
                          </h3>
                          <span className="label-uppercase bg-primary-100 text-primary-700 px-2 py-1 text-xs">
                            {patient.patient_id}
                          </span>
                        </div>
                        <p className="text-xs font-light text-neutral-500 mb-1">
                          {patient.age}y/o • {patient.gender}
                        </p>
                        <p className="text-xs font-light text-neutral-700 line-clamp-1">
                          {patient.condition}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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

