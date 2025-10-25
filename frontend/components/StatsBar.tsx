interface StatsBarProps {
  stats: {
    patients_monitored: number;
    daily_cost_savings: number;
  };
  alertCount: number;
}

export default function StatsBar({ stats, alertCount }: StatsBarProps) {
  return (
    <div className="flex gap-6">
      <StatCard
        label="Patients Monitored"
        value={stats.patients_monitored.toString()}
        color="blue"
      />
      <StatCard
        label="Active Alerts"
        value={alertCount.toString()}
        color={alertCount > 0 ? "red" : "green"}
      />
      <StatCard
        label="Daily Savings"
        value={`$${(stats.daily_cost_savings / 1000).toFixed(1)}K`}
        color="green"
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  color: "blue" | "red" | "green";
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    red: "bg-red-500/10 text-red-400 border-red-500/30",
    green: "bg-green-500/10 text-green-400 border-green-500/30",
  };

  return (
    <div className={`px-4 py-2 rounded-lg border ${colorClasses[color]}`}>
      <p className="text-xs opacity-80">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}

