import * as React from "react";
import { useState, useEffect, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  GitCompare,
  Filter,
  BarChart3,
  PieChart,
  RefreshCw,
  X,
  Star,
  Save,
  Trash2
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiUrl, getApiHeaders } from "@/lib/api-config";

interface BenchmarkData {
  velocity_fidelity: VelocityData[];
  ancilla_vs_swap: AncillaData[];
  cooling_strategies: CoolingData[];
  zoned_cycles: ZonedData[];
  sustainable_depth: DepthData[];
}

interface VelocityData {
  velocity: number;
  fidelity: number;
  decoherence: number;
  pLoss: number;
  zone: string;
}

interface AncillaData {
  circuit: string;
  swap_depth: number;
  ancilla_depth: number;
  reduction: number;
}

interface CoolingData {
  metric: string;
  greedy: number;
  conservative: number;
  adaptive: number;
}

interface ZonedData {
  cycle: number;
  d3: number;
  d5: number;
  d7: number;
}

interface DepthData {
  depth: number;
  fidelity: number;
  cumulativeLoss: number;
  harvardFraction: number;
}

type ChartType = "bar" | "radar";
type BenchmarkType = keyof BenchmarkData;

const BENCHMARK_OPTIONS = [
  { value: "ancilla_vs_swap", label: "Ancilla vs SWAP" },
  { value: "cooling_strategies", label: "Cooling Strategies" },
];

const METRIC_COLORS = {
  primary: "hsl(var(--primary))",
  secondary: "hsl(var(--secondary))",
  success: "hsl(var(--success))",
  warning: "hsl(var(--warning))",
  destructive: "hsl(var(--destructive))",
};

export function BenchmarkComparison() {
  const [data, setData] = useState<Partial<BenchmarkData>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkType>("ancilla_vs_swap");
  const [chartType, setChartType] = useState<ChartType>("bar");
  const [selectedCircuits, setSelectedCircuits] = useState<string[]>([]);
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(["greedy", "conservative", "adaptive"]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch favorites from backend
  const loadFavorites = async () => {
    try {
      const response = await fetch(apiUrl("/api/favorites/load"), {
        headers: getApiHeaders(),
      });
      if (response.ok) {
        const favs = await response.json();
        setFavorites(favs);
      }
    } catch (error) {
      console.error("Error loading favorites:", error);
    }
  };

  const handleSaveFavorite = async () => {
    setIsSaving(true);
    const config = {
      name: `Favorito ${selectedBenchmark === "ancilla_vs_swap" ? "Ancilla" : "Cooling"} ${new Date().toLocaleTimeString()}`,
      benchmark: selectedBenchmark,
      circuits: selectedCircuits,
      strategies: selectedStrategies,
      chartType: chartType
    };

    try {
      const response = await fetch(apiUrl("/api/favorites/save"), {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast({
          title: "Configuración Guardada",
          description: "Se ha añadido a tus favoritos",
        });
        loadFavorites();
      }
    } catch (error) {
      toast({
        title: "Error al guardar",
        description: "No se pudo conectar con el servidor",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const applyFavorite = (fav: any) => {
    setSelectedBenchmark(fav.benchmark);
    setSelectedCircuits(fav.circuits);
    setSelectedStrategies(fav.strategies);
    setChartType(fav.chartType);
    toast({
      title: "Configuración Cargada",
      description: fav.name,
    });
  };

  // Fetch benchmark data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [ancillaRes, coolingRes] = await Promise.all([
          fetch("/data/benchmark_ancilla_vs_swap.json"),
          fetch("/data/benchmark_cooling_strategies.json"),
        ]);

        const ancillaData = await ancillaRes.json();
        const coolingData = await coolingRes.json();

        setData({
          ancilla_vs_swap: ancillaData,
          cooling_strategies: coolingData,
        });

        // Initialize selected circuits
        if (ancillaData.length > 0) {
          setSelectedCircuits(ancillaData.map((d: AncillaData) => d.circuit));
        }
      } catch (error) {
        console.error("Failed to load benchmark data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    loadFavorites();
  }, []);

  // Filter data based on selections
  const filteredAncillaData = useMemo(() => {
    if (!data.ancilla_vs_swap) return [];
    return data.ancilla_vs_swap.filter((d) => selectedCircuits.includes(d.circuit));
  }, [data.ancilla_vs_swap, selectedCircuits]);

  const filteredCoolingData = useMemo(() => {
    if (!data.cooling_strategies) return [];
    return data.cooling_strategies;
  }, [data.cooling_strategies]);

  const toggleCircuit = (circuit: string) => {
    setSelectedCircuits((prev) =>
      prev.includes(circuit)
        ? prev.filter((c) => c !== circuit)
        : [...prev, circuit]
    );
  };

  const toggleStrategy = (strategy: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(strategy)
        ? prev.filter((s) => s !== strategy)
        : [...prev, strategy]
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="quantum-card p-3 shadow-lg border border-border bg-background">
          <p className="font-semibold mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex justify-between gap-4 text-sm">
              <span style={{ color: entry.color }}>{entry.name}:</span>
              <span className="font-mono">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderAncillaComparison = () => (
    <div className="space-y-4">
      {/* Filters */}
      <div className="p-4 rounded-lg bg-muted/30 border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filtrar Circuitos</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.ancilla_vs_swap?.map((d) => (
            <label
              key={d.circuit}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background border border-border cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <Checkbox
                checked={selectedCircuits.includes(d.circuit)}
                onCheckedChange={() => toggleCircuit(d.circuit)}
              />
              <span className="text-sm font-mono">{d.circuit}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={filteredAncillaData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />
            <XAxis dataKey="circuit" tick={{ fontSize: 12 }} />
            <YAxis
              label={{ value: "Profundidad", angle: -90, position: "insideLeft" }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar
              dataKey="swap_depth"
              name="SWAP Depth"
              fill={METRIC_COLORS.destructive}
              opacity={0.8}
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="ancilla_depth"
              name="Ancilla Depth"
              fill={METRIC_COLORS.success}
              opacity={0.9}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Reduction Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {filteredAncillaData.map((d) => (
          <div key={d.circuit} className="p-3 rounded-lg bg-muted/30 text-center">
            <p className="text-xs text-muted-foreground font-mono">{d.circuit}</p>
            <p className="text-xl font-bold text-success">{d.reduction}×</p>
            <p className="text-[10px] text-muted-foreground">reducción</p>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCoolingComparison = () => (
    <div className="space-y-4">
      {/* Strategy Toggles */}
      <div className="p-4 rounded-lg bg-muted/30 border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Estrategias a Comparar</span>
        </div>
        <div className="flex flex-wrap gap-3">
          {["greedy", "conservative", "adaptive"].map((strategy) => (
            <label
              key={strategy}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer transition-all ${selectedStrategies.includes(strategy)
                ? strategy === "adaptive"
                  ? "bg-success/10 border-success text-success"
                  : strategy === "conservative"
                    ? "bg-primary/10 border-primary text-primary"
                    : "bg-destructive/10 border-destructive text-destructive"
                : "bg-background border-border text-muted-foreground"
                }`}
            >
              <Checkbox
                checked={selectedStrategies.includes(strategy)}
                onCheckedChange={() => toggleStrategy(strategy)}
              />
              <span className="text-sm font-medium capitalize">{strategy}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Chart Type Toggle */}
      <div className="flex gap-2">
        <Button
          variant={chartType === "bar" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("bar")}
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          Barras
        </Button>
        <Button
          variant={chartType === "radar" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("radar")}
        >
          <PieChart className="w-4 h-4 mr-2" />
          Radar
        </Button>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "radar" ? (
            <RadarChart data={filteredCoolingData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
              <PolarGrid className="stroke-muted/30" />
              <PolarAngleAxis
                dataKey="metric"
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              {selectedStrategies.includes("greedy") && (
                <Radar
                  name="Greedy"
                  dataKey="greedy"
                  stroke={METRIC_COLORS.destructive}
                  fill={METRIC_COLORS.destructive}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              )}
              {selectedStrategies.includes("conservative") && (
                <Radar
                  name="Conservative"
                  dataKey="conservative"
                  stroke={METRIC_COLORS.primary}
                  fill={METRIC_COLORS.primary}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              )}
              {selectedStrategies.includes("adaptive") && (
                <Radar
                  name="Adaptive"
                  dataKey="adaptive"
                  stroke={METRIC_COLORS.success}
                  fill={METRIC_COLORS.success}
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
              )}
            </RadarChart>
          ) : (
            <BarChart data={filteredCoolingData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" />
              <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              {selectedStrategies.includes("greedy") && (
                <Bar dataKey="greedy" name="Greedy" fill={METRIC_COLORS.destructive} opacity={0.8} />
              )}
              {selectedStrategies.includes("conservative") && (
                <Bar dataKey="conservative" name="Conservative" fill={METRIC_COLORS.primary} opacity={0.8} />
              )}
              {selectedStrategies.includes("adaptive") && (
                <Bar dataKey="adaptive" name="Adaptive" fill={METRIC_COLORS.success} opacity={0.9} />
              )}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Strategy Summary */}
      <div className="grid grid-cols-3 gap-4">
        {selectedStrategies.map((strategy) => {
          const total = filteredCoolingData.reduce(
            (sum, d) => sum + (d[strategy as keyof CoolingData] as number || 0),
            0
          );
          const avg = (total / filteredCoolingData.length).toFixed(1);
          return (
            <div
              key={strategy}
              className={`p-4 rounded-lg border-2 ${strategy === "adaptive"
                ? "border-success/50 bg-success/5"
                : strategy === "conservative"
                  ? "border-primary/50 bg-primary/5"
                  : "border-destructive/50 bg-destructive/5"
                }`}
            >
              <p className="text-sm font-medium capitalize">{strategy}</p>
              <p className="text-2xl font-bold font-mono">{avg}%</p>
              <p className="text-xs text-muted-foreground">Promedio general</p>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="quantum-card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-quantum-glow/10 flex items-center justify-center">
            <GitCompare className="w-5 h-5 text-quantum-glow" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Comparación de Benchmarks</h3>
            <p className="text-sm text-muted-foreground">
              Análisis lado a lado con filtros interactivos
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {favorites.length > 3 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Star className="w-4 h-4 mr-2" />
                  Favoritos ({favorites.length})
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-background border border-border">
                <DropdownMenuLabel>Cargar Configuración</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {favorites.map((fav) => (
                  <DropdownMenuItem key={fav.id} onClick={() => applyFavorite(fav)}>
                    <span className="truncate">{fav.name}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveFavorite}
            disabled={isSaving}
          >
            {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Guardar
          </Button>

          <Select value={selectedBenchmark} onValueChange={(v) => setSelectedBenchmark(v as BenchmarkType)}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Seleccionar benchmark" />
            </SelectTrigger>
            <SelectContent className="bg-background border border-border z-50">
              {BENCHMARK_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Favorites Quick List (if many) */}
      {favorites.length > 0 && favorites.length <= 3 && (
        <div className="flex flex-wrap gap-2 p-2 bg-muted/20 rounded-lg">
          <span className="text-xs font-medium self-center px-2 text-muted-foreground flex items-center">
            <Star className="w-3 h-3 mr-1" /> Favoritos:
          </span>
          {favorites.map((fav) => (
            <Badge
              key={fav.id}
              variant="secondary"
              className="cursor-pointer hover:bg-primary/20 transition-colors"
              onClick={() => applyFavorite(fav)}
            >
              {fav.name}
            </Badge>
          ))}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="h-80 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : (
        <>
          {selectedBenchmark === "ancilla_vs_swap" && renderAncillaComparison()}
          {selectedBenchmark === "cooling_strategies" && renderCoolingComparison()}
        </>
      )}
    </div>
  );
}

export default BenchmarkComparison;
