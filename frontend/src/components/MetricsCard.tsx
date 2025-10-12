interface MetricsCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle: string;
  color: 'green' | 'blue' | 'purple' | 'yellow';
}

const colorConfig = {
  green: {
    bg: 'bg-green-500/10',
    icon: 'text-green-500',
    value: 'text-green-400'
  },
  blue: {
    bg: 'bg-blue-500/10',
    icon: 'text-blue-500',
    value: 'text-blue-400'
  },
  purple: {
    bg: 'bg-purple-500/10',
    icon: 'text-purple-500',
    value: 'text-purple-400'
  },
  yellow: {
    bg: 'bg-yellow-500/10',
    icon: 'text-yellow-500',
    value: 'text-yellow-400'
  }
};

const MetricsCard = ({ icon, title, value, subtitle, color }: MetricsCardProps) => {
  const config = colorConfig[color];

  return (
    <div className="backdrop-blur-lg bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 hover:border-slate-600 transition-all duration-200">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${config.bg}`}>
          <div className={config.icon}>
            {icon}
          </div>
        </div>
      </div>

      <div>
        <p className="text-sm text-slate-400 mb-1">{title}</p>
        <p className={`text-3xl font-bold mb-1 ${config.value}`}>
          {value}
        </p>
        <p className="text-xs text-slate-500">{subtitle}</p>
      </div>
    </div>
  );
};

export default MetricsCard;
