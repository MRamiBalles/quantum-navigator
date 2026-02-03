import { useState } from "react";
import { 
  BarChart3, 
  TrendingUp, 
  Zap, 
  Thermometer, 
  Layers,
  Download,
  RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { VelocityFidelityChart } from "./charts/VelocityFidelityChart";
import { AncillaVsSwapChart } from "./charts/AncillaVsSwapChart";
import { CoolingStrategiesChart } from "./charts/CoolingStrategiesChart";
import { ZonedCyclesChart } from "./charts/ZonedCyclesChart";

export function BenchmarkResults() {
  const [activeTab, setActiveTab] = useState("velocity");
  const [isRunning, setIsRunning] = useState(false);

  const handleRunBenchmarks = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 2000);
  };

  const handleExportResults = () => {
    const results = {
      timestamp: new Date().toISOString(),
      benchmarks: {
        velocity_fidelity: { max_velocity: 0.55, fidelity_threshold: 0.99 },
        ancilla_vs_swap: { reduction_factor: "2.8x-27x" },
        cooling_strategies: ["greedy", "conservative", "adaptive"],
        zoned_cycles: { surface_code_distance: [3, 5, 7] }
      }
    };
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "benchmark_results.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-quantum-glow/10 flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-quantum-glow" />
          </div>
          <div>
            <h1 className="text-2xl font-bold quantum-text">Benchmark Results</h1>
            <p className="text-muted-foreground">
              Análisis de rendimiento FPQA • Heating Model • Flying Ancillas
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRunBenchmarks}
            disabled={isRunning}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRunning ? 'animate-spin' : ''}`} />
            {isRunning ? "Ejecutando..." : "Ejecutar Benchmarks"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportResults}>
            <Download className="w-4 h-4 mr-2" />
            Exportar CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          icon={TrendingUp}
          title="Velocidad Límite"
          value="0.55 µm/µs"
          description="Umbral de calentamiento"
          status="success"
        />
        <SummaryCard
          icon={Zap}
          title="Reducción AOD"
          value="2.8×-27×"
          description="vs cadenas SWAP"
          status="success"
        />
        <SummaryCard
          icon={Thermometer}
          title="Mejor Estrategia"
          value="Adaptive"
          description="Cooling dinámico"
          status="success"
        />
        <SummaryCard
          icon={Layers}
          title="Surface Code"
          value="d=3,5,7"
          description="Ciclos zonificados"
          status="success"
        />
      </div>

      {/* Benchmark Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="velocity" className="gap-2">
            <TrendingUp className="w-4 h-4" />
            Velocidad
          </TabsTrigger>
          <TabsTrigger value="ancilla" className="gap-2">
            <Zap className="w-4 h-4" />
            Ancilla vs SWAP
          </TabsTrigger>
          <TabsTrigger value="cooling" className="gap-2">
            <Thermometer className="w-4 h-4" />
            Cooling
          </TabsTrigger>
          <TabsTrigger value="zoned" className="gap-2">
            <Layers className="w-4 h-4" />
            Zoned Cycles
          </TabsTrigger>
        </TabsList>

        <TabsContent value="velocity" className="mt-6">
          <VelocityFidelityChart />
        </TabsContent>

        <TabsContent value="ancilla" className="mt-6">
          <AncillaVsSwapChart />
        </TabsContent>

        <TabsContent value="cooling" className="mt-6">
          <CoolingStrategiesChart />
        </TabsContent>

        <TabsContent value="zoned" className="mt-6">
          <ZonedCyclesChart />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface SummaryCardProps {
  icon: React.ElementType;
  title: string;
  value: string;
  description: string;
  status: "success" | "warning" | "error";
}

function SummaryCard({ icon: Icon, title, value, description, status }: SummaryCardProps) {
  return (
    <div className="quantum-card p-4">
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <Badge 
          variant="outline" 
          className={
            status === "success" ? "text-success border-success/30" :
            status === "warning" ? "text-warning border-warning/30" :
            "text-destructive border-destructive/30"
          }
        >
          {status === "success" ? "✓" : status === "warning" ? "⚠" : "✗"}
        </Badge>
      </div>
      <div className="mt-3">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold font-mono quantum-text">{value}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

export default BenchmarkResults;
