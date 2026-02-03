import * as React from "react";
import { useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Zap,
  Thermometer,
  Layers,
  Download,
  RefreshCw,
  Infinity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { VelocityFidelityChart } from "./charts/VelocityFidelityChart";
import { AncillaVsSwapChart } from "./charts/AncillaVsSwapChart";
import { CoolingStrategiesChart } from "./charts/CoolingStrategiesChart";
import { ZonedCyclesChart } from "./charts/ZonedCyclesChart";
import { SustainableDepthChart } from "./charts/SustainableDepthChart";

export function BenchmarkResults() {
  const [activeTab, setActiveTab] = useState("velocity");
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleRunBenchmarks = () => {
    setIsRunning(true);
    setProgress(0);

    // Simulate real-time execution progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + 5;
      });
    }, 100);
  };

  const handleExportResults = () => {
    const results = {
      timestamp: new Date().toISOString(),
      version: "4.0",
      benchmarks: {
        velocity_fidelity: { max_velocity: 0.55, fidelity_threshold: 0.99 },
        ancilla_vs_swap: { reduction_factor: "2.8x-27x" },
        cooling_strategies: ["greedy", "conservative", "adaptive"],
        zoned_cycles: { surface_code_distance: [3, 5, 7] },
        sustainable_depth: { harvard_rate: "30k atoms/s", max_depth: 2100 }
      }
    };
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark_results_v4_${new Date().getTime()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-quantum-glow/10 flex items-center justify-center border border-quantum-glow/20 shadow-[0_0_15px_rgba(0,194,255,0.1)]">
            <BarChart3 className="w-6 h-6 text-quantum-glow" />
          </div>
          <div>
            <h1 className="text-2xl font-bold quantum-text tracking-tight">Benchmark Results</h1>
            <p className="text-muted-foreground flex items-center gap-2">
              <Badge variant="secondary" className="bg-primary/5 text-primary border-primary/10">v4.0</Badge>
              Análisis FPQA Hardware-Aware • Harvard/MIT 2025
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isRunning && (
            <div className="flex items-center gap-2 mr-4 animate-in slide-in-from-right-4">
              <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-quantum-glow transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs font-mono text-quantum-glow">{progress}%</span>
            </div>
          )}
          <Button
            variant="default"
            size="sm"
            onClick={handleRunBenchmarks}
            disabled={isRunning}
            className="bg-primary hover:bg-primary/90 shadow-[0_0_15px_rgba(var(--primary),0.3)]"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRunning ? 'animate-spin' : ''}`} />
            {isRunning ? "Simulando..." : "Ejecutar Full Suite"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportResults} className="hover:bg-primary/5">
            <Download className="w-4 h-4 mr-2" />
            Reporte JSON
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <SummaryCard
          icon={TrendingUp}
          title="Velocidad Límite"
          value="0.55 µm/µs"
          description="Umbral de calentamiento"
          status="success"
          delay={100}
        />
        <SummaryCard
          icon={Zap}
          title="Reducción AOD"
          value="24.2×"
          description="vs SWAP (QFT-8)"
          status="success"
          delay={200}
        />
        <SummaryCard
          icon={Thermometer}
          title="Optimal Cooling"
          value="Adaptive"
          description="Deep circuits crossover"
          status="success"
          delay={300}
        />
        <SummaryCard
          icon={Layers}
          title="Lifetime d=7"
          value=">50 ciclos"
          description="Retención de qubits"
          status="success"
          delay={400}
        />
        <SummaryCard
          icon={Infinity}
          title="Sustainable Depth"
          value="2100 layers"
          description="v=0.40 µm/µs"
          status="success"
          delay={500}
        />
      </div>

      {/* Benchmark Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-5 w-full max-w-3xl bg-muted/30 p-1 border border-border/40">
          <TabsTrigger value="velocity" className="gap-2 transition-all duration-300 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <TrendingUp className="w-4 h-4" />
            <span className="hidden sm:inline">Velocidad</span>
          </TabsTrigger>
          <TabsTrigger value="ancilla" className="gap-2 transition-all duration-300 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Zap className="w-4 h-4" />
            <span className="hidden sm:inline">Ancilla</span>
          </TabsTrigger>
          <TabsTrigger value="cooling" className="gap-2 transition-all duration-300 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Thermometer className="w-4 h-4" />
            <span className="hidden sm:inline">Cooling</span>
          </TabsTrigger>
          <TabsTrigger value="zoned" className="gap-2 transition-all duration-300 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Layers className="w-4 h-4" />
            <span className="hidden sm:inline">Zoned</span>
          </TabsTrigger>
          <TabsTrigger value="sustainable" className="gap-2 transition-all duration-300 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Infinity className="w-4 h-4" />
            <span className="hidden sm:inline">Depth</span>
          </TabsTrigger>
        </TabsList>

        <div className="relative mt-6 min-h-[500px]">
          <TabsContent value="velocity" className="animate-in fade-in slide-in-from-bottom-4 duration-500 absolute inset-0 m-0">
            <VelocityFidelityChart />
          </TabsContent>

          <TabsContent value="ancilla" className="animate-in fade-in slide-in-from-bottom-4 duration-500 absolute inset-0 m-0">
            <AncillaVsSwapChart />
          </TabsContent>

          <TabsContent value="cooling" className="animate-in fade-in slide-in-from-bottom-4 duration-500 absolute inset-0 m-0">
            <CoolingStrategiesChart />
          </TabsContent>

          <TabsContent value="zoned" className="animate-in fade-in slide-in-from-bottom-4 duration-500 absolute inset-0 m-0">
            <ZonedCyclesChart />
          </TabsContent>

          <TabsContent value="sustainable" className="animate-in fade-in slide-in-from-bottom-4 duration-500 absolute inset-0 m-0">
            <SustainableDepthChart />
          </TabsContent>
        </div>
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
  delay?: number;
}

function SummaryCard({ icon: Icon, title, value, description, status, delay = 0 }: SummaryCardProps) {
  return (
    <div
      className="quantum-card p-4 group hover:border-primary/50 transition-all duration-500 hover:shadow-[0_0_20px_rgba(0,194,255,0.15)] hover:-translate-y-1 animate-in fade-in zoom-in-95 duration-700"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
          <Icon className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
        </div>
        <Badge
          variant="outline"
          className={
            status === "success" ? "text-success border-success/30 bg-success/5" :
              status === "warning" ? "text-warning border-warning/30 bg-warning/5" :
                "text-destructive border-destructive/30 bg-destructive/5"
          }
        >
          {status === "success" ? "✓" : status === "warning" ? "⚠" : "✗"}
        </Badge>
      </div>
      <div className="mt-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold font-mono quantum-text mt-0.5 group-hover:text-primary transition-colors">{value}</p>
        <p className="text-xs text-muted-foreground mt-1 line-clamp-1 group-hover:text-muted-foreground/80">{description}</p>
      </div>
    </div>
  );
}

export default BenchmarkResults;
