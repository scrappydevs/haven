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

      {/* Alert Severity Scale */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider">Alert Severity</p>
        <div className="relative">
          {/* Gradient Bar */}
          <div className="h-8 rounded-md overflow-hidden flex">
            <div className="flex-1 bg-green-500" title="Low"></div>
            <div className="flex-1 bg-yellow-500" title="Medium"></div>
            <div className="flex-1 bg-orange-500" title="High"></div>
            <div className="flex-1 bg-red-500" title="Critical"></div>
          </div>
          {/* Labels */}
          <div className="flex justify-between mt-1.5 px-1">
            <span className="text-[10px] font-light text-neutral-500">Low</span>
            <span className="text-[10px] font-light text-neutral-500">Medium</span>
            <span className="text-[10px] font-light text-neutral-500">High</span>
            <span className="text-[10px] font-light text-neutral-500">Critical</span>
          </div>
        </div>
      </div>

      {/* Other Indicators */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider">Room Status</p>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-neutral-200 rounded-sm"></div>
            <span className="text-[11px] font-light text-neutral-600">Empty</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded-sm"></div>
            <span className="text-[11px] font-light text-neutral-600">Nurse Station</span>
          </div>
        </div>
      </div>
    </div>
  );
}

