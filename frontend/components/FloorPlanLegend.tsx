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
        <div className="border-l-2 border-primary-700 pl-2">
          <p className="text-[10px] font-light text-neutral-400 mb-0.5">Occupied</p>
          <p className="text-lg font-light text-neutral-950">
            {occupiedRooms}/{totalRooms}
          </p>
        </div>
        <div className="border-l-2 border-primary-400 pl-2">
          <p className="text-[10px] font-light text-neutral-400 mb-0.5">Occupancy</p>
          <p className="text-lg font-light text-neutral-950">
            {occupancyRate.toFixed(0)}%
          </p>
        </div>
        <div className="border-l-2 border-accent-terra pl-2">
          <p className="text-[10px] font-light text-neutral-400 mb-0.5">Nurses</p>
          <p className="text-lg font-light text-neutral-950">
            {totalNurses}
          </p>
        </div>
      </div>

      {/* Legend Items */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-primary-700 flex items-center justify-center">
            <span className="text-white text-[8px]">✓</span>
          </div>
          <span className="text-[10px] font-light text-neutral-600">Occupied</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-neutral-200 flex items-center justify-center">
            <span className="text-neutral-400 text-[10px]">+</span>
          </div>
          <span className="text-[10px] font-light text-neutral-600">Empty</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-accent-terra flex items-center justify-center">
            <span className="text-white text-[10px]">+</span>
          </div>
          <span className="text-[10px] font-light text-neutral-600">Nurse Station</span>
        </div>
      </div>

      {/* Quick Actions */}
      <button
        className="w-full border border-neutral-300 px-3 py-2 text-[10px] font-light hover:bg-neutral-50 transition-colors"
        onClick={() => window.location.reload()}
      >
        Reset View
      </button>
    </div>
  );
}

