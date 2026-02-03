import * as React from "react";
import { useState, useEffect, useRef, useCallback } from "react";
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
  GitCompare,
  AlertTriangle,
  Activity,
  Atom,
  StopCircle
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

// WebSocket Telemetry Interface (Harvard/QuEra 2025)
interface TelemetryPayload {
  status: "CONNECTING" | "RUNNING" | "COMPLETED" | "STOPPED" | "ERROR";
  percentage: number;
  cycle: number;
  atoms_lost: number;
  n_vib: number;
  fidelity: number;
  decoder_backlog_ms: number;
  timestamp: string;
}

export function BenchmarkResults() {
  const [activeTab, setActiveTab] = useState("velocity");
  const [isRunning, setIsRunning] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // WebSocket Telemetry State
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [wsStatus, setWsStatus] = useState<"disconnected" | "connected" | "error">("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(`gui_${Date.now()}`);

  // WebSocket Connection Handler
  const connectWebSocket = useCallback(() => {
    const clientId = clientIdRef.current;
    const ws = new WebSocket(`ws://localhost:8000/ws/benchmarks/${clientId}`);

    ws.onopen = () => {
      setWsStatus("connected");
      // Send start command
      const benchmarkType = BENCHMARK_MAP[activeTab] || "velocity_fidelity";
      ws.send(JSON.stringify({ benchmark_type: benchmarkType, cycles: 50 }));
    };

    ws.onmessage = (event) => {
      const data: TelemetryPayload = JSON.parse(event.data);
      setTelemetry(data);

      // Check for decoder backlog warning (>10ms = critical)
      if (data.decoder_backlog_ms > 10) {
        toast({
          title: "⚠️ Decoder Backlog Detectado",
          description: `Latencia: ${data.decoder_backlog_ms.toFixed(1)}ms`,
          variant: "destructive",
        });
      }

      // Check for completion
      if (data.status === "COMPLETED" || data.status === "STOPPED") {
        setIsRunning(false);
        setWsStatus("disconnected");
        toast({
          title: data.status === "COMPLETED" ? "✓ Benchmark Completado" : "Benchmark Detenido",
          description: `Ciclos: ${data.cycle} | Fidelidad: ${(data.fidelity * 100).toFixed(2)}%`,
        });
      }
    };

    ws.onerror = () => {
      setWsStatus("error");
      setIsRunning(false);
      toast({
        title: "Error de Conexión",
        description: "No se pudo conectar al servidor WebSocket",
        variant: "destructive",
      });
    };

    ws.onclose = () => {
      setWsStatus("disconnected");
    };

    wsRef.current = ws;
  }, [activeTab]);

  // Handle Run Benchmarks (WebSocket mode)
  const handleRunBenchmarks = () => {
    if (isRunning) return;
    setIsRunning(true);
    setTelemetry(null);
    clientIdRef.current = `gui_${Date.now()}`;
    connectWebSocket();
  };

  // Handle Stop Benchmarks
  const handleStopBenchmarks = async () => {
    try {
      await fetch(`http://localhost:8000/ws/benchmarks/${clientIdRef.current}/stop`, {
        method: "POST"
      });
    } catch (e) {
      console.error("Stop error:", e);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);


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
          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleStopBenchmarks}
            >
              <StopCircle className="w-4 h-4 mr-2" />
              Detener
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRunBenchmarks}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Ejecutar Benchmarks
            </Button>
          )}
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

      {/* Real-time Telemetry Panel (Harvard/QuEra 2025) */}
      {(isRunning || telemetry) && (
        <div className="p-4 rounded-xl border border-quantum-glow/30 bg-gradient-to-r from-quantum-glow/5 to-transparent">
          <div className="flex items-center gap-4 mb-3">
            <Activity className="w-5 h-5 text-quantum-glow animate-pulse" />
            <span className="font-semibold text-sm">Telemetría en Tiempo Real</span>
            <Badge variant="outline" className="ml-auto">
              {telemetry?.status || "CONNECTING"}
            </Badge>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>Ciclo {telemetry?.cycle || 0} / 50</span>
              <span>{(telemetry?.percentage || 0).toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-quantum-glow transition-all duration-300"
                style={{ width: `${telemetry?.percentage || 0}%` }}
              />
            </div>
          </div>

          {/* Physics Gauges */}
          <div className="grid grid-cols-4 gap-3">
            {/* n_vib (Heating) */}
            <div className={`p-3 rounded-lg border ${(telemetry?.n_vib || 0) > 1.2 ? 'border-destructive bg-destructive/5 animate-pulse' : 'border-border bg-muted/30'}`}>
              <div className="flex items-center gap-2 mb-1">
                <Thermometer className="w-4 h-4 text-warning" />
                <span className="text-xs font-medium">n_vib</span>
              </div>
              <p className="text-lg font-mono font-bold">{telemetry?.n_vib?.toFixed(2) || "0.00"}</p>
              <p className="text-[10px] text-muted-foreground">Heating (umbral: 1.5)</p>
            </div>

            {/* Atoms Lost */}
            <div className={`p-3 rounded-lg border ${(telemetry?.atoms_lost || 0) > 0 ? 'border-warning bg-warning/5' : 'border-border bg-muted/30'}`}>
              <div className="flex items-center gap-2 mb-1">
                <Atom className="w-4 h-4 text-primary" />
                <span className="text-xs font-medium">Átomos</span>
              </div>
              <p className="text-lg font-mono font-bold">{telemetry?.atoms_lost || 0}</p>
              <p className="text-[10px] text-muted-foreground">Perdidos (acumulado)</p>
            </div>

            {/* Fidelity */}
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-success" />
                <span className="text-xs font-medium">Fidelidad</span>
              </div>
              <p className="text-lg font-mono font-bold">{((telemetry?.fidelity || 1) * 100).toFixed(3)}%</p>
              <p className="text-[10px] text-muted-foreground">Lógica actual</p>
            </div>

            {/* Decoder Backlog */}
            <div className={`p-3 rounded-lg border ${(telemetry?.decoder_backlog_ms || 0) > 10 ? 'border-destructive bg-destructive/10 animate-pulse' : 'border-border bg-muted/30'}`}>
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-destructive" />
                <span className="text-xs font-medium">Backlog</span>
              </div>
              <p className="text-lg font-mono font-bold">{telemetry?.decoder_backlog_ms?.toFixed(1) || "0.0"}ms</p>
              <p className="text-[10px] text-muted-foreground">Decoder latency</p>
            </div>
          </div>
        </div>
      )}

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
