import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ChevronDown, 
  ChevronUp, 
  Cpu, 
  Database, 
  Layers, 
  Workflow,
  Zap,
  ArrowRight,
  GitBranch,
  Box
} from "lucide-react";

interface ArchitectureDiagramProps {
  onNavigate?: (module: string) => void;
}

export const ArchitectureDiagram = ({ onNavigate }: ArchitectureDiagramProps) => {
  const [expandedLayer, setExpandedLayer] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const layers = [
    {
      id: "frontend",
      name: "Frontend Layer",
      icon: Layers,
      color: "from-cyan-500/20 to-cyan-600/10",
      borderColor: "border-cyan-500/50",
      description: "React + TypeScript + Tailwind CSS",
      components: [
        { id: "dashboard", name: "Dashboard", module: "dashboard" },
        { id: "atom-editor", name: "Atom Register Editor", module: "neutral-atom" },
        { id: "benchmarks-ui", name: "Benchmark Visualization", module: "benchmarks" },
        { id: "gnn-viz", name: "GNN Decoder Analysis", module: "gnn-decoder" },
      ]
    },
    {
      id: "api",
      name: "API Layer",
      icon: Workflow,
      color: "from-purple-500/20 to-purple-600/10",
      borderColor: "border-purple-500/50",
      description: "FastAPI + WebSocket + REST",
      components: [
        { id: "rest", name: "REST Endpoints", path: "/api/*" },
        { id: "ws", name: "WebSocket Telemetry", path: "/ws/benchmarks" },
        { id: "auth", name: "API Key Auth", path: "X-API-Key" },
        { id: "cors", name: "CORS Middleware", path: "Origins" },
      ]
    },
    {
      id: "core",
      name: "Core Engine",
      icon: Cpu,
      color: "from-blue-500/20 to-blue-600/10",
      borderColor: "border-blue-500/50",
      description: "Optimization + Validation + Export",
      components: [
        { id: "optimizer", name: "SpectralAOD Router", detail: "Sabre + Cost Function" },
        { id: "validator", name: "Physics Validator", detail: "Heating Model" },
        { id: "bloqade", name: "Bloqade Exporter", detail: "Julia/QuEra" },
        { id: "openqasm", name: "OpenQASM 3.0", detail: "IBM/Google" },
      ]
    },
    {
      id: "physics",
      name: "Physics Layer",
      icon: Zap,
      color: "from-amber-500/20 to-amber-600/10",
      borderColor: "border-amber-500/50",
      description: "Neutral Atom + QEC + QRAM",
      components: [
        { id: "heating", name: "Heating Model", detail: "∆n_vib ∝ v³" },
        { id: "gnn", name: "GNN Decoder", detail: "~420ns FPGA" },
        { id: "phononic", name: "Phononic QRAM", detail: "SAW Routing" },
        { id: "qec", name: "QEC Simulation", detail: "Stim + PyMatching" },
      ]
    },
  ];

  const connections = [
    { from: "frontend", to: "api", label: "HTTP/WS" },
    { from: "api", to: "core", label: "Python" },
    { from: "core", to: "physics", label: "NumPy/SciPy" },
  ];

  const toggleLayer = (layerId: string) => {
    setExpandedLayer(expandedLayer === layerId ? null : layerId);
  };

  return (
    <Card className="quantum-card overflow-hidden">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <GitBranch className="w-5 h-5 text-cyan-400" />
          Arquitectura del Sistema
          <Badge variant="outline" className="ml-auto text-xs">
            Interactivo
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Mermaid-style diagram */}
        <div className="relative">
          {layers.map((layer, index) => (
            <div key={layer.id} className="relative">
              {/* Connection line to next layer */}
              {index < layers.length - 1 && (
                <div className="absolute left-1/2 -translate-x-1/2 top-full h-6 flex flex-col items-center z-0">
                  <div className="w-px h-4 bg-gradient-to-b from-muted-foreground/50 to-muted-foreground/20" />
                  <ArrowRight className="w-3 h-3 text-muted-foreground/50 rotate-90" />
                  <span className="text-[10px] text-muted-foreground/60 absolute -right-8 top-1">
                    {connections[index]?.label}
                  </span>
                </div>
              )}
              
              {/* Layer card */}
              <div
                className={`
                  relative z-10 mb-6 rounded-lg border bg-gradient-to-r ${layer.color} ${layer.borderColor}
                  transition-all duration-300 cursor-pointer
                  ${expandedLayer === layer.id ? 'ring-2 ring-cyan-500/30' : 'hover:ring-1 hover:ring-cyan-500/20'}
                `}
                onClick={() => toggleLayer(layer.id)}
                onMouseEnter={() => setHoveredNode(layer.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-md bg-background/50 ${hoveredNode === layer.id ? 'animate-pulse' : ''}`}>
                      <layer.icon className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <h3 className="font-medium text-sm">{layer.name}</h3>
                      <p className="text-xs text-muted-foreground">{layer.description}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    {expandedLayer === layer.id ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                
                {/* Expanded content */}
                {expandedLayer === layer.id && (
                  <div className="border-t border-border/50 p-3 animate-fade-in">
                    <div className="grid grid-cols-2 gap-2">
                      {layer.components.map((component) => (
                        <div
                          key={component.id}
                          className={`
                            p-2 rounded-md bg-background/30 border border-border/30
                            hover:bg-background/50 hover:border-cyan-500/30 transition-colors
                            ${component.module ? 'cursor-pointer' : ''}
                          `}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (component.module && onNavigate) {
                              onNavigate(component.module);
                            }
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <Box className="w-3 h-3 text-cyan-400/70" />
                            <span className="text-xs font-medium">{component.name}</span>
                          </div>
                          {'detail' in component && (
                            <p className="text-[10px] text-muted-foreground mt-1 ml-5">
                              {component.detail}
                            </p>
                          )}
                          {'path' in component && (
                            <p className="text-[10px] text-cyan-400/70 font-mono mt-1 ml-5">
                              {component.path}
                            </p>
                          )}
                          {component.module && (
                            <Badge variant="secondary" className="text-[9px] mt-1 ml-5">
                              Click to open
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30">
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-cyan-500/50" />
            <span>Frontend</span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-purple-500/50" />
            <span>API</span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-blue-500/50" />
            <span>Core</span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-amber-500/50" />
            <span>Physics</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-2 pt-2">
          <div className="text-center p-2 rounded-md bg-muted/30">
            <div className="text-lg font-bold text-cyan-400">4</div>
            <div className="text-[10px] text-muted-foreground">Capas</div>
          </div>
          <div className="text-center p-2 rounded-md bg-muted/30">
            <div className="text-lg font-bold text-purple-400">16</div>
            <div className="text-[10px] text-muted-foreground">Componentes</div>
          </div>
          <div className="text-center p-2 rounded-md bg-muted/30">
            <div className="text-lg font-bold text-blue-400">2</div>
            <div className="text-[10px] text-muted-foreground">Exporters</div>
          </div>
          <div className="text-center p-2 rounded-md bg-muted/30">
            <div className="text-lg font-bold text-amber-400">~420</div>
            <div className="text-[10px] text-muted-foreground">ns GNN</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
