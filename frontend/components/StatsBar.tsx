interface StatsBarProps {
  stats: {
    patients_monitored: number;
  };
  alertCount: number;
}

export default function StatsBar({ stats, alertCount }: StatsBarProps) {
  return (
    <div className="flex gap-4 justify-end w-full max-w-md">
      <StatCard
        label="Patients Monitored"
        value={stats.patients_monitored.toString()}
        accentColor="primary"
        width="flex-1"
      />
      <StatCard
        label="Active Alerts"
        value={alertCount.toString()}
        accentColor={alertCount > 0 ? "alert" : "primary"}
        width="flex-[0.8]"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  accentColor: "primary" | "alert";
  width: string;
}

function StatCard({ label, value, accentColor, width }: StatCardProps) {
  const borderClass = accentColor === "alert" 
    ? "border-l-4 border-accent-terra" 
    : "border-l-4 border-primary-700";

  return (
    <div className={`bg-surface border border-neutral-200 ${borderClass} px-4 py-3 ${width} rounded-lg`}>
      <div className="flex items-center gap-2">
        <p className="text-neutral-500 text-sm font-light label-uppercase">{label}</p>
        {/* add a gap that right justifies the value */}
        <div className="flex-1"></div>
          <p className="text-sm font-light text-neutral-950">{value}</p>
      </div>
    </div>
  );
}
