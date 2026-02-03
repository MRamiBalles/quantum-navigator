import { TrendingUp, TrendingDown } from "lucide-react";

interface DataPoint {
  label: string;
  value: number;
  previous: number;
}

const data: DataPoint[] = [
  { label: "Lun", value: 23, previous: 28 },
  { label: "Mar", value: 31, previous: 25 },
  { label: "Mié", value: 28, previous: 32 },
  { label: "Jue", value: 45, previous: 38 },
  { label: "Vie", value: 52, previous: 42 },
  { label: "Sáb", value: 38, previous: 35 },
  { label: "Hoy", value: 47, previous: 40 },
];

const maxValue = Math.max(...data.map(d => Math.max(d.value, d.previous)));

export function MetricsChart() {
  const avgImprovement = data.reduce((acc, d) => acc + ((d.value - d.previous) / d.previous * 100), 0) / data.length;

  return (
    <div className="quantum-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Rendimiento de Optimización</h3>
          <p className="text-sm text-muted-foreground">Reducción de profundidad de circuito</p>
        </div>
        <div className="flex items-center gap-2 text-success">
          <TrendingUp className="w-4 h-4" />
          <span className="text-sm font-medium">+{avgImprovement.toFixed(1)}%</span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-48">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-xs text-muted-foreground font-mono">
          <span>{maxValue}</span>
          <span>{Math.round(maxValue / 2)}</span>
          <span>0</span>
        </div>

        {/* Chart area */}
        <div className="ml-8 h-full flex items-end gap-2">
          {data.map((point, index) => (
            <div key={index} className="flex-1 flex flex-col items-center gap-2">
              <div className="relative w-full flex justify-center gap-1" style={{ height: "calc(100% - 24px)" }}>
                {/* Previous value bar */}
                <div 
                  className="w-3 rounded-t bg-muted-foreground/30 transition-all duration-500"
                  style={{ height: `${(point.previous / maxValue) * 100}%` }}
                />
                {/* Current value bar */}
                <div 
                  className="w-3 rounded-t bg-primary transition-all duration-500 hover:bg-primary/80"
                  style={{ 
                    height: `${(point.value / maxValue) * 100}%`,
                    animationDelay: `${index * 100}ms`
                  }}
                />
              </div>
              <span className="text-xs text-muted-foreground">{point.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-border">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-primary" />
          <span className="text-xs text-muted-foreground">Optimizado (LightSABRE)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-muted-foreground/30" />
          <span className="text-xs text-muted-foreground">Qiskit Estándar</span>
        </div>
      </div>
    </div>
  );
}
