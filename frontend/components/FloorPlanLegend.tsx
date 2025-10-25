'use client';

interface FloorPlanLegendProps {
  totalRooms: number;
  occupiedRooms: number;
  totalNurses: number;
}

export default function FloorPlanLegend({ totalRooms, occupiedRooms, totalNurses }: FloorPlanLegendProps) {
  const occupancyRate = totalRooms > 0 ? (occupiedRooms / totalRooms) * 100 : 0;

  return (
    <div className="bg-surface border border-neutral-200 p-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6 pb-6 border-b border-neutral-200">
        <div className="border-l-4 border-primary-700 pl-4">
          <p className="label-uppercase text-neutral-500 mb-1">Occupied</p>
          <p className="text-2xl font-extralight tracking-tight text-neutral-950">
            {occupiedRooms}/{totalRooms}
          </p>
        </div>
        <div className="border-l-4 border-primary-400 pl-4">
          <p className="label-uppercase text-neutral-500 mb-1">Occupancy</p>
          <p className="text-2xl font-extralight tracking-tight text-neutral-950">
            {occupancyRate.toFixed(0)}%
          </p>
        </div>
        <div className="border-l-4 border-accent-terra pl-4">
          <p className="label-uppercase text-neutral-500 mb-1">Nurses</p>
          <p className="text-2xl font-extralight tracking-tight text-neutral-950">
            {totalNurses}
          </p>
        </div>
      </div>

      {/* Legend */}
      <div>
        <h4 className="label-uppercase text-neutral-700 mb-4">Legend</h4>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-primary-700 border border-neutral-950 flex items-center justify-center">
              <span className="text-white text-xs">✓</span>
            </div>
            <span className="text-sm font-light text-neutral-700">Patient Room (Occupied)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-neutral-100 border border-neutral-300 flex items-center justify-center">
              <span className="text-neutral-400 text-sm">+</span>
            </div>
            <span className="text-sm font-light text-neutral-700">Patient Room (Empty)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-accent-terra border border-neutral-950 flex items-center justify-center">
              <span className="text-white text-lg">+</span>
            </div>
            <span className="text-sm font-light text-neutral-700">Nurse Station</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-6 border-t border-neutral-200">
        <button
          className="w-full border-2 border-neutral-950 px-6 py-3 font-normal text-xs uppercase tracking-widest hover:bg-neutral-950 hover:text-white transition-all"
          onClick={() => {
            // Refresh or reset functionality
            window.location.reload();
          }}
        >
          Reset View
        </button>
      </div>
    </div>
  );
}

