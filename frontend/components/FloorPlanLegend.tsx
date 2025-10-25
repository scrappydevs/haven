'use client';

interface FloorPlanLegendProps {
  totalRooms: number;
  occupiedRooms: number;
  totalNurses: number;
}

export default function FloorPlanLegend({ totalRooms, occupiedRooms, totalNurses }: FloorPlanLegendProps) {
  const occupancyRate = totalRooms > 0 ? (occupiedRooms / totalRooms) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="border-l-2 border-primary-700 pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Occupied</p>
          <p className="text-2xl font-light text-neutral-950">
            {occupiedRooms}/{totalRooms}
          </p>
        </div>
        <div className="border-l-2 border-primary-400 pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Occupancy</p>
          <p className="text-2xl font-light text-neutral-950">
            {occupancyRate.toFixed(0)}%
          </p>
        </div>
        <div className="border-l-2 border-accent-terra pl-3">
          <p className="text-xs font-light text-neutral-500 mb-1">Nurses</p>
          <p className="text-2xl font-light text-neutral-950">
            {totalNurses}
          </p>
        </div>
      </div>

      {/* Legend Items */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-primary-700 flex items-center justify-center rounded">
            <span className="text-white text-xs">✓</span>
          </div>
          <span className="text-xs font-light text-neutral-950">Occupied</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-neutral-200 flex items-center justify-center rounded">
            <span className="text-neutral-400 text-sm">+</span>
          </div>
          <span className="text-xs font-light text-neutral-950">Empty</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 bg-accent-terra flex items-center justify-center rounded">
            <span className="text-white text-sm">+</span>
          </div>
          <span className="text-xs font-light text-neutral-950">Nurse Station</span>
        </div>
      </div>

      {/* Quick Actions */}
      <button
        className="w-full border border-neutral-200 px-4 py-2.5 text-xs font-light text-neutral-950 hover:bg-neutral-50 transition-colors rounded-lg"
        onClick={() => window.location.reload()}
      >
        Reset View
      </button>
    </div>
  );
}

