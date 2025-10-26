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
    <div className="space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="border-l-2 border-primary-700 pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Occupied</p>
          <p className="text-xl font-light text-neutral-950">
            {occupiedRooms}/{totalRooms}
          </p>
        </div>
        <div className="border-l-2 border-primary-400 pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Occupancy</p>
          <p className="text-xl font-light text-neutral-950">
            {occupancyRate.toFixed(0)}%
          </p>
        </div>
        <div className="border-l-2 border-blue-500 pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Stations</p>
          <p className="text-xl font-light text-neutral-950">
            {nurseStations}
          </p>
        </div>
        <div className="border-l-2 border-accent-terra pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Nurses</p>
          <p className="text-xl font-light text-neutral-950">
            {totalNurses}
          </p>
        </div>
      </div>

      {/* Legend Items */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-neutral-200 flex items-center justify-center rounded-sm">
            <span className="text-neutral-400 text-xs">+</span>
          </div>
          <span className="text-xs font-light text-neutral-600">Empty Room</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-green-500 flex items-center justify-center rounded-sm">
            <span className="text-white text-xs">✓</span>
          </div>
          <span className="text-xs font-light text-neutral-600">Normal - No Alerts</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-yellow-500 flex items-center justify-center rounded-sm">
            <span className="text-white text-xs font-bold">!</span>
          </div>
          <span className="text-xs font-light text-neutral-600">Medium Alert</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-orange-500 flex items-center justify-center rounded-sm">
            <span className="text-white text-xs font-bold">⚠</span>
          </div>
          <span className="text-xs font-light text-neutral-600">High Alert</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-red-500 flex items-center justify-center rounded-sm">
            <span className="text-white text-xs font-bold">●</span>
          </div>
          <span className="text-xs font-light text-neutral-600">Critical Alert</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-blue-500 flex items-center justify-center rounded-sm">
            <span className="text-white text-xs">◉</span>
          </div>
          <span className="text-xs font-light text-neutral-600">Nurse Station</span>
        </div>
      </div>
    </div>
  );
}

