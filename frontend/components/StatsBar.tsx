interface StatsBarProps {
  stats: {
    patients_monitored: number;
    daily_cost_savings: number;
  };
  alertCount: number;
}

export default function StatsBar({ stats, alertCount }: StatsBarProps) {
  return (
    <div className="flex gap-8">
      <StatCard
        label="Patients Monitored"
        value={stats.patients_monitored.toString()}
        accentColor="primary"
      />
      <StatCard
        label="Active Alerts"
        value={alertCount.toString()}
        accentColor={alertCount > 0 ? "alert" : "primary"}
      />
      <StatCard
        label="Daily Savings"
        value={`$${(stats.daily_cost_savings / 1000).toFixed(1)}K`}
        accentColor="primary"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  accentColor: "primary" | "alert";
}

function StatCard({ label, value, accentColor }: StatCardProps) {
  const borderClass = accentColor === "alert" 
    ? "border-l-4 border-accent-terra" 
    : "border-l-4 border-primary-700";

  return (
    <div className={`bg-surface border border-neutral-200 ${borderClass} px-6 py-4`}>
      <p className="label-uppercase text-neutral-500 mb-1">{label}</p>
      <p className="text-3xl font-extralight tracking-tight text-neutral-950">{value}</p>
    </div>
  );
}

