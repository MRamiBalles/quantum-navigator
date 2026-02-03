import { Activity, Thermometer, Atom, Timer, AlertTriangle, TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { PhysicsTelemetry, TelemetryAlerts } from "@/hooks/useBenchmarkWebSocket";

interface TelemetryPanelProps {
  telemetry: PhysicsTelemetry | null;
  alerts: TelemetryAlerts | null;
  progress: number;
  isRunning: boolean;
}

interface GaugeProps {
  label: string;
  value: number | string;
  unit: string;
  icon: React.ElementType;
  warning?: boolean;
  critical?: boolean;
  max?: number;
}

function Gauge({ label, value, unit, icon: Icon, warning, critical, max }: GaugeProps) {
  const numValue = typeof value === "number" ? value : 0;
  const percentage = max ? (numValue / max) * 100 : 0;
  
  return (
    <div 
      className={cn(
        "p-3 rounded-lg border transition-all duration-200",
        critical ? "border-destructive/50 bg-destructive/10 animate-pulse" :
        warning ? "border-warning/50 bg-warning/10" :
        "border-border/50 bg-muted/30"
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn(
          "w-4 h-4",
          critical ? "text-destructive" :
          warning ? "text-warning" :
          "text-muted-foreground"
        )} />
        <span className="text-xs text-muted-foreground">{label}</span>
        {(warning || critical) && (
          <AlertTriangle className={cn(
            "w-3 h-3 ml-auto",
            critical ? "text-destructive" : "text-warning"
          )} />
        )}
      </div>
      <div className="flex items-baseline gap-1">
        <span className={cn(
          "text-2xl font-mono font-bold",
          critical ? "text-destructive" :
          warning ? "text-warning" :
          "text-foreground"
        )}>
          {typeof value === "number" ? value.toFixed(2) : value}
        </span>
        <span className="text-xs text-muted-foreground">{unit}</span>
      </div>
      {max && (
        <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
          <div 
            className={cn(
              "h-full transition-all duration-200",
              critical ? "bg-destructive" :
              warning ? "bg-warning" :
              "bg-primary"
            )}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function TelemetryPanel({ telemetry, alerts, progress, isRunning }: TelemetryPanelProps) {
  if (!isRunning && !telemetry) {
    return (
      <div className="p-4 rounded-lg border border-dashed border-border/50 bg-muted/20">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Activity className="w-5 h-5" />
          <div>
            <p className="text-sm font-medium">Telemetría en tiempo real</p>
            <p className="text-xs">Ejecuta un benchmark para ver los indicadores físicos</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Progreso de ejecución</span>
          <span className="font-mono font-medium">{progress.toFixed(0)}%</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Physics Gauges Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Gauge
          label="n_vib (calentamiento)"
          value={telemetry?.n_vib ?? 0}
          unit="ℏω"
          icon={Thermometer}
          warning={alerts?.heating_warning}
          critical={(telemetry?.n_vib ?? 0) > 1.5}
          max={2}
        />
        <Gauge
          label="Pérdida de átomos"
          value={telemetry?.cumulative_atom_loss ?? 0}
          unit="átomos"
          icon={Atom}
          warning={(telemetry?.cumulative_atom_loss ?? 0) > 5}
          critical={(telemetry?.cumulative_atom_loss ?? 0) > 10}
        />
        <Gauge
          label="Fidelidad lógica"
          value={telemetry?.fidelity ?? 100}
          unit="%"
          icon={TrendingUp}
          warning={(telemetry?.fidelity ?? 100) < 97}
          critical={alerts?.fidelity_critical}
          max={100}
        />
        <Gauge
          label="Backlog decodificador"
          value={telemetry?.decoder_backlog_ms ?? 0}
          unit="ms"
          icon={Timer}
          warning={alerts?.backlog_warning}
          critical={(telemetry?.decoder_backlog_ms ?? 0) > 15}
          max={20}
        />
      </div>

      {/* Additional Metrics */}
      {telemetry && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t border-border/30">
          <span>Velocidad: <span className="font-mono text-foreground">{telemetry.velocity.toFixed(3)} µm/µs</span></span>
          <span>Temp: <span className="font-mono text-foreground">{telemetry.temperature_uk.toFixed(1)} µK</span></span>
          <span>Refill: <span className="font-mono text-foreground">{(telemetry.refill_rate / 1000).toFixed(0)}k/s</span></span>
        </div>
      )}
    </div>
  );
}
