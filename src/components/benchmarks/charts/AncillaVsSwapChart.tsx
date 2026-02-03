import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Zap, ArrowRight } from "lucide-react";

// Benchmark data: Ancilla vs SWAP gate comparison
const generateComparisonData = () => {
  const circuits = [
    { name: "QFT-8", qubits: 8 },
    { name: "QFT-16", qubits: 16 },
    { name: "QAOA-12", qubits: 12 },
    { name: "VQE-20", qubits: 20 },
    { name: "Grover-16", qubits: 16 },
    { name: "Surface-9", qubits: 9 }
  ];

  return circuits.map(circuit => {
    // SWAP chain model: O(n) SWAPs per remote gate
    const swapGates = Math.floor(circuit.qubits * 1.5 + Math.random() * circuit.qubits);
    const swapDepth = swapGates * 3; // Each SWAP = 3 CNOTs
    const swapTime = swapDepth * 50; // 50ns per CNOT layer
    
    // Flying ancilla model: 1-2 shuttles per remote gate
    const shuttleMoves = Math.floor(circuit.qubits * 0.3 + 2);
    const ancillaDepth = shuttleMoves * 2; // Shuttle + gate
    const ancillaTime = shuttleMoves * 80 + ancillaDepth * 20; // Shuttle time + gate time
    
    const reduction = (swapTime / ancillaTime).toFixed(1);
    
    return {
      circuit: circuit.name,
      qubits: circuit.qubits,
      swapGates,
      swapDepth,
      swapTime,
      shuttleMoves,
      ancillaDepth,
      ancillaTime,
      reduction: parseFloat(reduction),
      efficiency: ((1 - ancillaTime / swapTime) * 100).toFixed(1)
    };
  });
};

export function AncillaVsSwapChart() {
  const data = useMemo(() => generateComparisonData(), []);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0]?.payload;
      return (
        <div className="quantum-card p-4 shadow-lg min-w-64">
          <p className="font-semibold mb-2">{label}</p>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Qubits:</span>
              <span className="font-mono">{item.qubits}</span>
            </div>
            <div className="border-t border-border pt-2 mt-2">
              <p className="font-medium text-destructive mb-1">SWAP Chain:</p>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Puertas SWAP:</span>
                <span className="font-mono">{item.swapGates}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Profundidad:</span>
                <span className="font-mono">{item.swapDepth}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tiempo:</span>
                <span className="font-mono">{item.swapTime} ns</span>
              </div>
            </div>
            <div className="border-t border-border pt-2">
              <p className="font-medium text-success mb-1">Flying Ancilla:</p>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Shuttles:</span>
                <span className="font-mono">{item.shuttleMoves}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Profundidad:</span>
                <span className="font-mono">{item.ancillaDepth}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tiempo:</span>
                <span className="font-mono">{item.ancillaTime} ns</span>
              </div>
            </div>
            <div className="border-t border-border pt-2 flex items-center justify-between">
              <span className="font-medium">Reducción:</span>
              <Badge className="bg-success text-success-foreground">
                {item.reduction}× más rápido
              </Badge>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const avgReduction = (data.reduce((acc, d) => acc + d.reduction, 0) / data.length).toFixed(1);
  const maxReduction = Math.max(...data.map(d => d.reduction)).toFixed(1);
  const minReduction = Math.min(...data.map(d => d.reduction)).toFixed(1);

  return (
    <div className="quantum-card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Flying Ancilla vs SWAP Chains</h3>
          <p className="text-sm text-muted-foreground">
            Experimento B: Reducción de profundidad mediante ancilas móviles (AOD)
          </p>
        </div>
        <Badge variant="outline" className="font-mono">
          benchmark_ancilla_vs_swap.py
        </Badge>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg bg-muted/30">
          <p className="text-2xl font-bold font-mono text-primary">{avgReduction}×</p>
          <p className="text-xs text-muted-foreground">Reducción Promedio</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/30">
          <p className="text-2xl font-bold font-mono text-success">{maxReduction}×</p>
          <p className="text-xs text-muted-foreground">Máxima Reducción</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/30">
          <p className="text-2xl font-bold font-mono text-warning">{minReduction}×</p>
          <p className="text-xs text-muted-foreground">Mínima Reducción</p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />
            
            <XAxis 
              dataKey="circuit" 
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis 
              label={{ value: "Tiempo (ns)", angle: -90, position: "insideLeft" }}
              tick={{ fontSize: 12 }}
            />
            
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            <Bar 
              dataKey="swapTime" 
              name="SWAP Chain" 
              fill="hsl(var(--destructive))"
              opacity={0.8}
              radius={[4, 4, 0, 0]}
            />
            <Bar 
              dataKey="ancillaTime" 
              name="Flying Ancilla" 
              fill="hsl(var(--success))"
              opacity={0.9}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Strategy Explanation */}
      <div className="p-4 rounded-lg bg-muted/20 border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-5 h-5 text-quantum-purple" />
          <span className="font-semibold">Estrategia BUS (Buffered Unidirectional Shuttle)</span>
        </div>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex-1 p-3 rounded bg-destructive/10 border border-destructive/20">
            <p className="font-medium text-destructive">SWAP Chain (Superconductores)</p>
            <p className="text-xs text-muted-foreground mt-1">
              O(n) puertas SWAP × 3 CNOTs cada una
            </p>
          </div>
          
          <ArrowRight className="w-6 h-6 text-muted-foreground" />
          
          <div className="flex-1 p-3 rounded bg-success/10 border border-success/20">
            <p className="font-medium text-success">Flying Ancilla (FPQA)</p>
            <p className="text-xs text-muted-foreground mt-1">
              1-2 shuttles AOD + gate en zona de interacción
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AncillaVsSwapChart;
