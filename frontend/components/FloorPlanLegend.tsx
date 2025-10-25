'use client';

interface FloorPlanLegendProps {
  totalRooms: number;
  occupiedRooms: number;
  totalNurses: number;
  nurseStations?: number;
}

export default function FloorPlanLegend({ totalRooms, occupiedRooms, totalNurses, nurseStations = 0 }: FloorPlanLegendProps) {
  const occupancyRate = totalRooms > 0 ? (occupiedRooms / totalRooms) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-2">
        <div className="border-l-2 border-primary-700 pl-2">
          <p className="text-sm font-normal text-neutral-700 mb-1">Occupied</p>
          <p className="text-lg font-normal text-neutral-950">
            {occupiedRooms}/{totalRooms}
          </p>
        </div>
        <div className="border-l-2 border-primary-400 pl-2">
          <p className="text-sm font-normal text-neutral-700 mb-1">Occupancy</p>
          <p className="text-lg font-normal text-neutral-950">
            {occupancyRate.toFixed(0)}%
          </p>
        </div>
        <div className="border-l-2 border-blue-500 pl-2">
          <p className="text-sm font-normal text-neutral-700 mb-1">Stations</p>
          <p className="text-lg font-normal text-neutral-950">
            {nurseStations}
          </p>
        </div>
        <div className="border-l-2 border-accent-terra pl-2">
          <p className="text-sm font-normal text-neutral-700 mb-1">Nurses</p>
          <p className="text-lg font-normal text-neutral-950">
            {totalNurses}
          </p>
        </div>
      </div>

      {/* Legend Items */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 rounded bg-neutral-200 flex items-center justify-center">
            <span className="text-neutral-500 text-sm">+</span>
          </div>
          <span className="text-sm font-normal text-neutral-950">Empty Room</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 rounded" style={{ backgroundColor: '#95C7BB' }}></div>
          <span className="text-sm font-normal text-neutral-950">Occupied Room</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 rounded" style={{ backgroundColor: '#9ec3e6' }}></div>
          <span className="text-sm font-normal text-neutral-950">Nurse Station</span>
        </div>
      </div>
    </div>
  );
}

