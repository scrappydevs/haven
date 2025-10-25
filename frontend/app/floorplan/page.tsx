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

  // Initialize Smplrspace viewer
  useEffect(() => {
    if (!containerRef.current || !smplrLoaded || !window.smplr) return;

    let space: any = null;

    const initViewer = async () => {
      try {
        const smplr = window.smplr;

        // Get credentials from environment or use demo mode
        const spaceId = process.env.NEXT_PUBLIC_SMPLR_SPACE_ID || 'spc_demo';
        const clientToken = process.env.NEXT_PUBLIC_SMPLR_CLIENT_TOKEN || 'pub_demo';

        // Initialize space with your Smplrspace credentials
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
          onReady: () => {
            console.log('✅ Smplrspace viewer ready');
            setIsViewerReady(true);
            setViewerError(null);
            
            // Discover rooms from furniture in the floor plan
            const definition = space.getDefinition();
            console.log('📐 Space definition:', definition);
            
            // Extract furniture/equipment as patient rooms
            const furnitureRooms: Room[] = [];
            if (definition?.furniture && Array.isArray(definition.furniture)) {
              definition.furniture.forEach((furniture: any, index: number) => {
                const roomType = furniture.name?.toLowerCase().includes('nurse') || 
                               furniture.name?.toLowerCase().includes('station') 
                  ? 'nurse_station' 
                  : 'patient';
                
                furnitureRooms.push({
                  id: furniture.id || `furniture-${index}`,
                  name: furniture.name || `Room ${index + 1}`,
                  type: roomType,
                  position: {
                    levelIndex: furniture.levelIndex || 0,
                    x: furniture.position?.x || 0,
                    z: furniture.position?.z || 0,
                  },
                });
              });
            }
            
            if (furnitureRooms.length > 0) {
              console.log(`✅ Discovered ${furnitureRooms.length} rooms from floor plan`);
              setRooms(furnitureRooms);
            } else {
              console.log('⚠️ No furniture found in space, using demo rooms');
              // Fallback demo rooms
              setRooms([
                { id: 'room-101', name: 'Room 101', type: 'patient', position: { levelIndex: 0, x: -5, z: -5 } },
                { id: 'room-102', name: 'Room 102', type: 'patient', position: { levelIndex: 0, x: -5, z: 0 } },
                { id: 'room-103', name: 'Room 103', type: 'patient', position: { levelIndex: 0, x: -5, z: 5 } },
                { id: 'room-104', name: 'Room 104', type: 'patient', position: { levelIndex: 0, x: 5, z: -5 } },
                { id: 'room-105', name: 'Room 105', type: 'patient', position: { levelIndex: 0, x: 5, z: 0 } },
                { id: 'room-106', name: 'Room 106', type: 'patient', position: { levelIndex: 0, x: 5, z: 5 } },
              ]);
            }
          },
          onError: (error: string) => {
            console.error('❌ Viewer error:', error);
            setViewerError(error);
            setUseDemoMode(true);
            // Set demo rooms for fallback
            setRooms([
              { id: 'room-101', name: 'Room 101', type: 'patient', position: { levelIndex: 0, x: -5, z: -5 } },
              { id: 'room-102', name: 'Room 102', type: 'patient', position: { levelIndex: 0, x: -5, z: 0 } },
              { id: 'room-103', name: 'Room 103', type: 'patient', position: { levelIndex: 0, x: -5, z: 5 } },
              { id: 'room-104', name: 'Room 104', type: 'patient', position: { levelIndex: 0, x: 5, z: -5 } },
              { id: 'room-105', name: 'Room 105', type: 'patient', position: { levelIndex: 0, x: 5, z: 0 } },
              { id: 'room-106', name: 'Room 106', type: 'patient', position: { levelIndex: 0, x: 5, z: 5 } },
            ]);
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
      if (space) {
        space.remove();
      }
    };
  }, [smplrLoaded]);

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

  const assignPatientToRoom = (patient: SupabasePatient) => {
    if (!selectedRoom) return;

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
  };

  const unassignPatient = (roomId: string) => {
    setRooms(prev => prev.map(room => {
      if (room.id === roomId) {
        const { assignedPatient, ...rest } = room;
        return rest;
      }
      return room;
    }));
  };

  const assignedPatientIds = rooms
    .filter(r => r.assignedPatient)
    .map(r => r.assignedPatient!.patient_id);

  const filteredPatients = availablePatients.filter(
    p => !assignedPatientIds.includes(p.patient_id)
  );

  return (
    <>
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
          // Set demo rooms
          setRooms([
            { id: 'room-101', name: 'Room 101', type: 'patient', position: { levelIndex: 0, x: -5, z: -5 } },
            { id: 'room-102', name: 'Room 102', type: 'patient', position: { levelIndex: 0, x: -5, z: 0 } },
            { id: 'room-103', name: 'Room 103', type: 'patient', position: { levelIndex: 0, x: -5, z: 5 } },
            { id: 'room-104', name: 'Room 104', type: 'patient', position: { levelIndex: 0, x: 5, z: -5 } },
            { id: 'room-105', name: 'Room 105', type: 'patient', position: { levelIndex: 0, x: 5, z: 0 } },
            { id: 'room-106', name: 'Room 106', type: 'patient', position: { levelIndex: 0, x: 5, z: 5 } },
          ]);
        }}
      />
      <link href="https://app.smplrspace.com/lib/smplr.css" rel="stylesheet" />
      
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b-2 border-neutral-950 bg-surface">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-playfair font-black bg-gradient-to-r from-primary-950 to-primary-700 bg-clip-text text-transparent">
                Hospital Floor Plan
              </h1>
              <p className="text-xs label-uppercase text-neutral-500 mt-1">
                Interactive Room & Staff Management
              </p>
            </div>
            <div className="flex gap-4">
              <a
                href="/dashboard"
                className="border border-neutral-300 px-6 py-2 font-light text-xs uppercase tracking-wider text-neutral-700 hover:border-neutral-950 hover:text-neutral-950 transition-colors"
              >
                ← Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-6 p-6">
        {/* Floor Plan Viewer (Left - 8 columns) */}
        <div className="col-span-8 space-y-6">
          <div className="bg-surface border-2 border-neutral-950 p-6">
            <div className="mb-4 border-b-2 border-neutral-950 pb-3">
              <h2 className="text-xl font-light tracking-tight text-neutral-950">
                {useDemoMode ? '2D Floor Plan View (Demo Mode)' : '3D Floor Plan View'}
              </h2>
              <p className="text-sm font-light text-neutral-500 mt-1">
                Click rooms to assign patients • Click nurse stations to assign staff
              </p>
            </div>

            {/* Error Message */}
            {viewerError && (
              <div className="bg-accent-sand border-l-4 border-accent-terra p-4 mb-4">
                <p className="text-sm font-light text-neutral-950">
                  <span className="font-medium">Note:</span> {viewerError}
                </p>
                <p className="text-xs text-neutral-700 mt-2">
                  To enable 3D view, add your Smplrspace credentials to `.env.local`
                </p>
              </div>
            )}

            {/* Smplrspace Container or Demo Grid */}
            {useDemoMode ? (
              // Demo Mode: Simple 2D Grid
              <div className="w-full h-[600px] bg-neutral-50 border border-neutral-200 p-8">
                <div className="grid grid-cols-3 gap-6 h-full">
                  {rooms.filter(r => r.type === 'patient').map((room: Room) => (
                    <button
                      key={room.id}
                      onClick={() => {
                        setSelectedRoom(room);
                        if (!room.assignedPatient) {
                          setShowPatientModal(true);
                        }
                      }}
                      className={`border-2 p-6 transition-all hover:scale-105 ${
                        room.assignedPatient
                          ? 'bg-primary-100 border-primary-700'
                          : 'bg-surface border-neutral-300 hover:border-primary-700'
                      } ${selectedRoom?.id === room.id ? 'ring-2 ring-primary-700' : ''}`}
                    >
                      <div className="text-center">
                        <div className={`w-16 h-16 mx-auto mb-3 border-2 flex items-center justify-center ${
                          room.assignedPatient
                            ? 'bg-primary-700 border-primary-700'
                            : 'bg-neutral-100 border-neutral-300'
                        }`}>
                          {room.assignedPatient ? (
                            <img
                              src={room.assignedPatient.photo_url}
                              alt={room.assignedPatient.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <span className="text-2xl text-neutral-400">+</span>
                          )}
                        </div>
                        <p className="label-uppercase text-neutral-700 mb-2">{room.name}</p>
                        {room.assignedPatient ? (
                          <div>
                            <p className="text-sm font-light text-neutral-950 truncate">
                              {room.assignedPatient.name}
                            </p>
                            <p className="text-xs label-uppercase text-primary-700">
                              {room.assignedPatient.patient_id}
                            </p>
                          </div>
                        ) : (
                          <p className="text-xs label-uppercase text-neutral-400">Empty</p>
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
                className="w-full h-[600px] bg-neutral-50 border border-neutral-200"
                style={{ position: 'relative' }}
              />
            )}
          </div>

          {/* Legend */}
          <FloorPlanLegend
            totalRooms={rooms.filter(r => r.type === 'patient').length}
            occupiedRooms={rooms.filter(r => r.assignedPatient).length}
            totalNurses={rooms.reduce((sum, r) => sum + (r.assignedNurses?.length || 0), 0)}
          />
        </div>

        {/* Room Management Panel (Right - 4 columns) */}
        <div className="col-span-4">
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
            <div className="bg-surface border border-neutral-200">
              <div className="px-6 py-4 border-b-2 border-neutral-950">
                <h3 className="text-lg font-light tracking-tight text-neutral-950">
                  All Rooms
                </h3>
                <p className="text-sm font-light text-neutral-500 mt-1">
                  Click any room for details
                </p>
              </div>

              <div className="overflow-y-auto max-h-[calc(100vh-300px)]">
                {rooms.filter(r => r.type === 'patient').map((room: Room) => (
                  <div
                    key={room.id}
                    className={`border-b border-neutral-200 p-4 hover:bg-neutral-50 transition-colors cursor-pointer ${
                      selectedRoom?.id === room.id ? 'bg-primary-100' : ''
                    }`}
                    onClick={() => {
                      setSelectedRoom(room);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 ${
                          room.assignedPatient ? 'bg-primary-700' : 'bg-neutral-300'
                        }`} />
                        <div>
                          <p className="font-light text-neutral-950 text-sm">{room.name}</p>
                          {room.assignedPatient && (
                            <p className="text-xs label-uppercase text-primary-700">
                              {room.assignedPatient.patient_id}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="label-uppercase text-xs text-neutral-500">
                        {room.assignedPatient ? 'Occupied' : 'Empty'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
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

          <div className="relative bg-surface border-2 border-neutral-950 max-w-2xl w-full max-h-[80vh] overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b-2 border-neutral-950">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-light tracking-tight text-neutral-950">
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
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-200px)]">
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
                      className="flex items-start gap-4 p-4 bg-surface hover:bg-neutral-50 border border-neutral-200 hover:border-primary-700 transition-all text-left"
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

          <div className="relative bg-surface border-2 border-neutral-950 max-w-md w-full">
            <div className="p-6 border-b-2 border-neutral-950">
              <h2 className="text-xl font-light tracking-tight text-neutral-950">
                Manage {selectedRoom.name}
              </h2>
            </div>

            <div className="p-6">
              <p className="text-sm font-light text-neutral-500 mb-4">
                Nurse station management coming soon
              </p>
              <button
                onClick={() => {
                  setShowNurseModal(false);
                  setSelectedRoom(null);
                }}
                className="w-full border-2 border-neutral-950 px-6 py-3 font-normal text-xs uppercase tracking-widest hover:bg-neutral-950 hover:text-white transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}

