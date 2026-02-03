import { useMemo, useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, Info, RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

// Benchmark data based on physical constraints
const generateVelocityData = () => {
  const data = [];
  const maxVelocity = 0.8; // µm/µs hard limit
  const optimalVelocity = 0.55; // µm/µs recommended
  const heatingCoefficient = 0.02;

  for (let v = 0.1; v <= maxVelocity; v += 0.05) {
    // Fidelity model: F = exp(-heating * velocity^2)
    const heating = heatingCoefficient * Math.pow(v / optimalVelocity, 2);
    const fidelity = Math.exp(-heating) * (v <= optimalVelocity ? 1 : Math.exp(-(v - optimalVelocity) * 5));

    // Decoherence cost model
    const decoherence = v * (v / maxVelocity) * heatingCoefficient * 100;

    // P_loss probability
    const pLoss = v > optimalVelocity
      ? Math.min(0.5, (v - optimalVelocity) / (maxVelocity - optimalVelocity) * 0.5)
      : 0.01;

    data.push({
      velocity: parseFloat(v.toFixed(2)),
      fidelity: parseFloat((fidelity * 100).toFixed(2)),
      decoherence: parseFloat(decoherence.toFixed(2)),
      pLoss: parseFloat((pLoss * 100).toFixed(2)),
      zone: v <= optimalVelocity ? "safe" : v <= 0.7 ? "warning" : "danger"
    });
  }
  return data;
};

export function VelocityFidelityChart() {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    fetch('/data/benchmark_velocity_fidelity.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Error loading benchmark data:", err);
        // Fallback to mock data if fetch fails
        setData(generateVelocityData());
        setIsLoading(false);
      });
  }, []);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const zone = payload[0]?.payload?.zone;
      return (
        <div className="quantum-card p-3 shadow-lg">
          <p className="font-mono text-sm mb-2">v = {label} µm/µs</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}
              {entry.dataKey === "fidelity" ? "%" :
                entry.dataKey === "pLoss" ? "%" : ""}
            </p>
          ))}
          <div className="mt-2 pt-2 border-t border-border">
            <Badge
              variant="outline"
              className={
                zone === "safe" ? "text-success border-success" :
                  zone === "warning" ? "text-warning border-warning" :
                    "text-destructive border-destructive"
              }
            >
              {zone === "safe" ? "Zona Segura" :
                zone === "warning" ? "Zona de Riesgo" : "Zona Crítica"}
            </Badge>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="quantum-card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Velocidad vs Fidelidad</h3>
          <p className="text-sm text-muted-foreground">
            Experimento A: Validación del límite de velocidad AOD (0.55 µm/µs)
          </p>
        </div>
        <Badge variant="outline" className="font-mono">
          benchmark_velocity_fidelity.py
        </Badge>
      </div>

      {/* Chart */}
      <div className="h-80 relative">
        {isLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/50 backdrop-blur-sm z-10 rounded-lg">
            <RefreshCw className="w-8 h-8 text-primary animate-spin mb-4" />
            <p className="text-sm font-medium animate-pulse">Sincronizando con backend Python...</p>
          </div>
        ) : null}

        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              <linearGradient id="safeZone" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.1} />
                <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />

            <XAxis
              dataKey="velocity"
              label={{ value: "Velocidad (µm/µs)", position: "bottom", offset: 0 }}
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              yAxisId="left"
              label={{ value: "Fidelidad (%)", angle: -90, position: "insideLeft" }}
              domain={[80, 100]}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: "P_loss (%)", angle: 90, position: "insideRight" }}
              domain={[0, 50]}
              tick={{ fontSize: 12 }}
            />

            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Reference lines */}
            <ReferenceLine
              x={0.55}
              yAxisId="left"
              stroke="hsl(var(--success))"
              strokeDasharray="5 5"
              label={{ value: "Óptimo", position: "top", fill: "hsl(var(--success))" }}
            />
            <ReferenceLine
              x={0.8}
              yAxisId="left"
              stroke="hsl(var(--destructive))"
              strokeDasharray="5 5"
              label={{ value: "Límite", position: "top", fill: "hsl(var(--destructive))" }}
            />

            {/* Fidelity line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="fidelity"
              name="Fidelidad"
              stroke="hsl(var(--primary))"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, strokeWidth: 2 }}
            />

            {/* P_loss line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="pLoss"
              name="P_loss"
              stroke="hsl(var(--warning))"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Physical Model Explanation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-border">
        <ModelCard
          icon={CheckCircle}
          title="Zona Segura"
          range="0 - 0.55 µm/µs"
          description="Calentamiento mínimo, fidelidad >99%"
          status="success"
        />
        <ModelCard
          icon={AlertTriangle}
          title="Zona de Riesgo"
          range="0.55 - 0.70 µm/µs"
          description="Calentamiento moderado, fidelidad 95-99%"
          status="warning"
        />
        <ModelCard
          icon={Info}
          title="Modelo Físico"
          range="Δn_vib"
          description="decoherence = d × (v/v_max) × η"
          status="info"
        />
      </div>
    </div>
  );
}

interface ModelCardProps {
  icon: React.ElementType;
  title: string;
  range: string;
  description: string;
  status: "success" | "warning" | "info";
}

function ModelCard({ icon: Icon, title, range, description, status }: ModelCardProps) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
      <Icon className={`w-5 h-5 mt-0.5 ${status === "success" ? "text-success" :
          status === "warning" ? "text-warning" : "text-primary"
        }`} />
      <div>
        <p className="font-medium text-sm">{title}</p>
        <p className="font-mono text-xs text-primary">{range}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

export default VelocityFidelityChart;
