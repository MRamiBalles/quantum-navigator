import { useState } from "react";
import { 
  BarChart3, 
  TrendingUp, 
  Zap, 
  Thermometer, 
  Layers,
  Download,
  RefreshCw,
  Infinity,
  FileSpreadsheet,
  GitCompare
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "@/hooks/use-toast";
import { VelocityFidelityChart } from "./charts/VelocityFidelityChart";
import { AncillaVsSwapChart } from "./charts/AncillaVsSwapChart";
import { CoolingStrategiesChart } from "./charts/CoolingStrategiesChart";
import { ZonedCyclesChart } from "./charts/ZonedCyclesChart";
import { SustainableDepthChart } from "./charts/SustainableDepthChart";
import { BenchmarkComparison } from "./BenchmarkComparison";
import { exportBenchmarkToCsv, exportAllBenchmarks } from "./utils/exportCsv";

const BENCHMARK_MAP: Record<string, string> = {
  velocity: "velocity_fidelity",
  ancilla: "ancilla_vs_swap",
  cooling: "cooling_strategies",
  zoned: "zoned_cycles",
  sustainable: "sustainable_depth"
};

export function BenchmarkResults() {
  const [activeTab, setActiveTab] = useState("velocity");
  const [isRunning, setIsRunning] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleRunBenchmarks = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 2000);
  };

  const handleExportCurrent = async () => {
    setIsExporting(true);
    try {
      const benchmarkType = BENCHMARK_MAP[activeTab];
      await exportBenchmarkToCsv(benchmarkType);
      toast({
        title: "Exportación completada",
        description: `${benchmarkType}.csv descargado correctamente`,
      });
    } catch (error) {
      toast({
        title: "Error de exportación",
        description: "No se pudo exportar el benchmark actual",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportAll = async () => {
    setIsExporting(true);
    try {
      await exportAllBenchmarks();
      toast({
        title: "Exportación completa",
        description: "Todos los benchmarks exportados en JSON",
      });
    } catch (error) {
      toast({
        title: "Error de exportación",
        description: "No se pudo exportar todos los benchmarks",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
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
              Análisis de rendimiento FPQA • Heating Model • Flying Ancillas • v4.0 Continuous Operation
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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" disabled={isExporting}>
                {isExporting ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Download className="w-4 h-4 mr-2" />
                )}
                Exportar
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Opciones de Exportación</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleExportCurrent}>
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Exportar Tab Actual (CSV)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleExportAll}>
                <Download className="w-4 h-4 mr-2" />
                Exportar Todos (JSON)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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
        <SummaryCard
          icon={Infinity}
          title="Operación Continua"
          value="30k/s"
          description="Harvard/MIT 2025"
          status="success"
        />
      </div>

      {/* Benchmark Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-6 w-full max-w-4xl">
          <TabsTrigger value="velocity" className="gap-2">
            <TrendingUp className="w-4 h-4" />
            <span className="hidden sm:inline">Velocidad</span>
          </TabsTrigger>
          <TabsTrigger value="ancilla" className="gap-2">
            <Zap className="w-4 h-4" />
            <span className="hidden sm:inline">Ancilla</span>
          </TabsTrigger>
          <TabsTrigger value="cooling" className="gap-2">
            <Thermometer className="w-4 h-4" />
            <span className="hidden sm:inline">Cooling</span>
          </TabsTrigger>
          <TabsTrigger value="zoned" className="gap-2">
            <Layers className="w-4 h-4" />
            <span className="hidden sm:inline">Zoned</span>
          </TabsTrigger>
          <TabsTrigger value="sustainable" className="gap-2">
            <Infinity className="w-4 h-4" />
            <span className="hidden sm:inline">Depth</span>
          </TabsTrigger>
          <TabsTrigger value="compare" className="gap-2">
            <GitCompare className="w-4 h-4" />
            <span className="hidden sm:inline">Comparar</span>
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

        <TabsContent value="sustainable" className="mt-6">
          <SustainableDepthChart />
        </TabsContent>

        <TabsContent value="compare" className="mt-6">
          <BenchmarkComparison />
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
    <div className="quantum-card p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/10">
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
