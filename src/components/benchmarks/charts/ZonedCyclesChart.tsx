import * as React from "react";
import { useMemo, useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Layers, Grid3X3, ArrowDownUp, RefreshCw } from "lucide-react";

// Generate Surface Code cycle data
const generateZonedCycleData = () => {
  const distances = [3, 5, 7];
  const cycles = 20;

  const data = [];

  for (let cycle = 0; cycle <= cycles; cycle++) {
    const entry: any = { cycle };

    distances.forEach(d => {
      // Logical error rate decreases exponentially with distance
      const physicalError = 0.001; // 0.1% physical error rate
      const threshold = 0.01; // ~1% threshold
      const suppressionRatio = threshold / physicalError;

      // P_L ~ (p/p_th)^((d+1)/2) for p < p_th
      const baseLogicalError = Math.pow(1 / suppressionRatio, (d + 1) / 2);

      // Accumulate error over cycles (simplified model)
      const accumulatedError = 1 - Math.pow(1 - baseLogicalError, cycle + 1);

      entry[`d${d}`] = parseFloat((accumulatedError * 100).toFixed(4));
      entry[`d${d}_fidelity`] = parseFloat(((1 - accumulatedError) * 100).toFixed(2));
    });

    data.push(entry);
  }

  return data;
};

// Zone architecture visualization data
const zoneArchitecture = [
  { zone: "STORAGE", atoms: 50, purpose: "Qubits de datos entre operaciones", color: "primary" },
  { zone: "ENTANGLEMENT", atoms: 9, purpose: "Ejecución de gates CZ/CNOT", color: "success" },
  { zone: "READOUT", atoms: 16, purpose: "Medición de síndromes", color: "warning" },
  { zone: "RESERVOIR", atoms: 20, purpose: "Átomos de reemplazo", color: "muted-foreground" }
];

export function ZonedCyclesChart() {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDistance, setSelectedDistance] = useState<number | null>(null);

  useEffect(() => {
    setIsLoading(true);
    fetch('/data/benchmark_zoned_cycles.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Error loading benchmark data:", err);
        setData(generateZonedCycleData());
        setIsLoading(false);
      });
  }, []);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="quantum-card p-4 shadow-lg">
          <p className="font-semibold mb-2">Ciclo {label}</p>
          <div className="space-y-2">
            {payload.map((entry: any, index: number) => {
              const distance = entry.dataKey.replace('d', '').replace('_fidelity', '');
              return (
                <div key={index} className="flex justify-between gap-4 text-sm">
                  <span style={{ color: entry.color }}>
                    d={distance}:
                  </span>
                  <span className="font-mono">
                    {entry.dataKey.includes('fidelity')
                      ? `${entry.value.toFixed(2)}% fidelidad`
                      : `${entry.value.toFixed(4)}% error`
                    }
                  </span>
                </div>
              );
            })}
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
          <h3 className="text-lg font-semibold">Ciclos de Surface Code Zonificado</h3>
          <p className="text-sm text-muted-foreground">
            Experimento D: Evolución del error lógico en arquitectura FPQA zonificada
          </p>
        </div>
        <Badge variant="outline" className="font-mono">
          benchmark_zoned_cycles.py
        </Badge>
      </div>

      {/* Distance Selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">Distancia del código:</span>
        <div className="flex gap-2">
          {[3, 5, 7].map(d => (
            <button
              key={d}
              onClick={() => setSelectedDistance(selectedDistance === d ? null : d)}
              className={`px-3 py-1 rounded-lg text-sm font-mono transition-colors ${selectedDistance === d
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
                }`}
            >
              d={d}
            </button>
          ))}
        </div>
        <Badge variant="secondary" className="ml-auto">
          <Grid3X3 className="w-3 h-3 mr-1" />
          {selectedDistance ? `${selectedDistance}×${selectedDistance} = ${selectedDistance * selectedDistance} qubits` : "Todos"}
        </Badge>
      </div>

      {/* Error Rate Chart */}
      <div className="h-72 relative">
        {isLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/50 backdrop-blur-sm z-10 rounded-lg">
            <RefreshCw className="w-8 h-8 text-primary animate-spin mb-4" />
            <p className="text-sm font-medium animate-pulse">Calculando ciclos QEC...</p>
          </div>
        ) : null}

        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              <linearGradient id="colorD3" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorD5" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--warning))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--warning))" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorD7" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />

            <XAxis
              dataKey="cycle"
              label={{ value: "Ciclo QEC", position: "bottom", offset: 0 }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: "Error Lógico (%)", angle: -90, position: "insideLeft" }}
              tick={{ fontSize: 12 }}
              scale="log"
              domain={['auto', 'auto']}
            />

            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {(!selectedDistance || selectedDistance === 3) && (
              <Area
                type="monotone"
                dataKey="d3"
                name="d=3"
                stroke="hsl(var(--destructive))"
                fill="url(#colorD3)"
                strokeWidth={2}
              />
            )}
            {(!selectedDistance || selectedDistance === 5) && (
              <Area
                type="monotone"
                dataKey="d5"
                name="d=5"
                stroke="hsl(var(--warning))"
                fill="url(#colorD5)"
                strokeWidth={2}
              />
            )}
            {(!selectedDistance || selectedDistance === 7) && (
              <Area
                type="monotone"
                dataKey="d7"
                name="d=7"
                stroke="hsl(var(--success))"
                fill="url(#colorD7)"
                strokeWidth={2}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Zone Architecture */}
      <div className="pt-4 border-t border-border">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="w-5 h-5 text-quantum-purple" />
          <span className="font-semibold">Arquitectura de Zonas FPQA</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {zoneArchitecture.map((zone) => (
            <div
              key={zone.zone}
              className="p-3 rounded-lg bg-muted/30 border border-border"
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-mono text-${zone.color}`}>
                  {zone.zone}
                </span>
                <Badge variant="outline" className="text-[10px]">
                  {zone.atoms} átomos
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                {zone.purpose}
              </p>
            </div>
          ))}
        </div>

        {/* Shuttle Flow Diagram */}
        <div className="mt-4 p-4 rounded-lg bg-muted/20 border border-dashed border-border">
          <div className="flex items-center justify-center gap-4 text-sm">
            <div className="text-center">
              <div className="w-16 h-10 rounded bg-primary/20 border border-primary/50 flex items-center justify-center mb-1">
                <span className="text-[10px] font-mono">STORAGE</span>
              </div>
            </div>
            <ArrowDownUp className="w-5 h-5 text-muted-foreground" />
            <div className="text-center">
              <div className="w-16 h-10 rounded bg-success/20 border border-success/50 flex items-center justify-center mb-1">
                <span className="text-[10px] font-mono">ENTANGLE</span>
              </div>
            </div>
            <ArrowDownUp className="w-5 h-5 text-muted-foreground" />
            <div className="text-center">
              <div className="w-16 h-10 rounded bg-warning/20 border border-warning/50 flex items-center justify-center mb-1">
                <span className="text-[10px] font-mono">READOUT</span>
              </div>
            </div>
          </div>
          <p className="text-center text-[10px] text-muted-foreground mt-2">
            Flujo de shuttle AOD para ciclo QEC completo
          </p>
        </div>
      </div>
    </div>
  );
}

export default ZonedCyclesChart;
