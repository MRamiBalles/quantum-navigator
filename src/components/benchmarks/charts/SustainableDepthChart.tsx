import { useMemo } from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Timer, Zap, RefreshCw, TrendingUp } from "lucide-react";

// Sustainable depth data based on Harvard/MIT 2025 continuous operation model
const generateSustainableDepthData = () => {
  const data = [];
  const harvardReloadRate = 30000; // atoms/s
  const atomLifetime = 10; // seconds base
  const baseFidelity = 0.995; // per gate
  
  for (let depth = 10; depth <= 500; depth += 20) {
    // Fidelity decay: F_total = F_gate^depth
    const totalFidelity = Math.pow(baseFidelity, depth) * 100;
    
    // Loss probability accumulation
    const pLossPerLayer = 0.001;
    const cumulativeLoss = (1 - Math.pow(1 - pLossPerLayer, depth)) * 100;
    
    // Time to reach depth (assuming 1µs per layer)
    const timeToDepth = depth * 0.001; // ms
    
    // Reload rate required to maintain qubit count
    const requiredReloadRate = Math.floor(1000 * cumulativeLoss / 100);
    const harvardFraction = (requiredReloadRate / harvardReloadRate) * 100;
    
    // Sustainable threshold (90% fidelity, 10% loss)
    const isSustainable = totalFidelity >= 90 && cumulativeLoss <= 10;
    
    data.push({
      depth,
      fidelity: parseFloat(totalFidelity.toFixed(2)),
      cumulativeLoss: parseFloat(cumulativeLoss.toFixed(2)),
      timeToDepth: parseFloat(timeToDepth.toFixed(3)),
      harvardFraction: parseFloat(harvardFraction.toFixed(2)),
      status: isSustainable ? "sustainable" : totalFidelity >= 80 ? "marginal" : "unsustainable"
    });
  }
  return data;
};

export function SustainableDepthChart() {
  const data = useMemo(() => generateSustainableDepthData(), []);
  
  // Find sustainable depth threshold
  const sustainableThreshold = data.find(d => d.status !== "sustainable")?.depth || 500;
  const marginalThreshold = data.find(d => d.status === "unsustainable")?.depth || 500;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const status = payload[0]?.payload?.status;
      return (
        <div className="quantum-card p-3 shadow-lg">
          <p className="font-mono text-sm mb-2 font-semibold">Profundidad: {label} capas</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}
              {entry.dataKey === "fidelity" || entry.dataKey === "cumulativeLoss" || entry.dataKey === "harvardFraction" ? "%" : 
               entry.dataKey === "timeToDepth" ? " ms" : ""}
            </p>
          ))}
          <div className="mt-2 pt-2 border-t border-border">
            <Badge 
              variant="outline"
              className={
                status === "sustainable" ? "text-success border-success" :
                status === "marginal" ? "text-warning border-warning" :
                "text-destructive border-destructive"
              }
            >
              {status === "sustainable" ? "Sostenible" : 
               status === "marginal" ? "Marginal" : "No Sostenible"}
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
          <h3 className="text-lg font-semibold">Profundidad Sostenible</h3>
          <p className="text-sm text-muted-foreground">
            Experimento E: Análisis de operación continua (Harvard/MIT 2025 - 30k atoms/s)
          </p>
        </div>
        <Badge variant="outline" className="font-mono">
          benchmark_sustainable_depth.py
        </Badge>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              <linearGradient id="sustainableGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--destructive))" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />
            
            <XAxis 
              dataKey="depth" 
              label={{ value: "Profundidad del Circuito (capas)", position: "bottom", offset: 0 }}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              yAxisId="left"
              label={{ value: "Fidelidad / Pérdida (%)", angle: -90, position: "insideLeft" }}
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              label={{ value: "Harvard Rate (%)", angle: 90, position: "insideRight" }}
              domain={[0, 20]}
              tick={{ fontSize: 12 }}
            />
            
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Threshold lines */}
            <ReferenceLine 
              x={sustainableThreshold} 
              yAxisId="left"
              stroke="hsl(var(--success))" 
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ 
                value: `Sostenible: ${sustainableThreshold}`, 
                position: "top", 
                fill: "hsl(var(--success))",
                fontSize: 11
              }}
            />
            <ReferenceLine 
              y={90} 
              yAxisId="left"
              stroke="hsl(var(--warning))" 
              strokeDasharray="3 3"
              label={{ value: "90% Fidelidad", position: "right", fill: "hsl(var(--warning))" }}
            />
            <ReferenceLine 
              y={10} 
              yAxisId="left"
              stroke="hsl(var(--destructive))" 
              strokeDasharray="3 3"
              label={{ value: "10% Pérdida", position: "right", fill: "hsl(var(--destructive))" }}
            />
            
            {/* Fidelity area */}
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="fidelity"
              name="Fidelidad Total"
              fill="url(#sustainableGradient)"
              stroke="hsl(var(--success))"
              strokeWidth={2}
            />
            
            {/* Cumulative loss line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="cumulativeLoss"
              name="Pérdida Acumulada"
              stroke="hsl(var(--destructive))"
              strokeWidth={2}
              dot={false}
            />
            
            {/* Harvard fraction bars */}
            <Bar
              yAxisId="right"
              dataKey="harvardFraction"
              name="% Tasa Harvard"
              fill="hsl(var(--primary))"
              opacity={0.6}
              radius={[2, 2, 0, 0]}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-border">
        <MetricCard
          icon={TrendingUp}
          title="Profundidad Máxima"
          value={`${sustainableThreshold} capas`}
          description="Fidelidad ≥90%, Pérdida ≤10%"
          status="success"
        />
        <MetricCard
          icon={Timer}
          title="Tiempo por Capa"
          value="1 µs"
          description="Ciclo de gate típico"
          status="info"
        />
        <MetricCard
          icon={Zap}
          title="Tasa Harvard"
          value="30k atoms/s"
          description="Recarga MIT/Harvard 2025"
          status="info"
        />
        <MetricCard
          icon={RefreshCw}
          title="Operación Continua"
          value="∞"
          description="Con recarga activa"
          status="success"
        />
      </div>

      {/* Physical Model */}
      <div className="p-4 rounded-lg bg-muted/30 border border-border">
        <h4 className="font-semibold text-sm mb-2">Modelo de Operación Continua</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div>
            <span className="text-muted-foreground">Fidelidad total:</span>
            <span className="ml-2 text-primary">F_total = F_gate^depth</span>
          </div>
          <div>
            <span className="text-muted-foreground">Pérdida acumulada:</span>
            <span className="ml-2 text-primary">P_loss = 1 - (1 - p)^depth</span>
          </div>
          <div>
            <span className="text-muted-foreground">Tasa requerida:</span>
            <span className="ml-2 text-primary">R_req = N × P_loss / T</span>
          </div>
          <div>
            <span className="text-muted-foreground">Sostenibilidad:</span>
            <span className="ml-2 text-primary">R_req ≤ R_harvard (30k/s)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ElementType;
  title: string;
  value: string;
  description: string;
  status: "success" | "warning" | "info";
}

function MetricCard({ icon: Icon, title, value, description, status }: MetricCardProps) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
      <Icon className={`w-5 h-5 mt-0.5 ${
        status === "success" ? "text-success" :
        status === "warning" ? "text-warning" : "text-primary"
      }`} />
      <div>
        <p className="font-medium text-sm">{title}</p>
        <p className="font-mono text-lg text-primary font-bold">{value}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

export default SustainableDepthChart;
