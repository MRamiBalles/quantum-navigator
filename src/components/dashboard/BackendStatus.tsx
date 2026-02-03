import { Server, Cloud, Cpu, CheckCircle, XCircle, Clock, Atom, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

type BackendType = "superconductor" | "neutral-atom" | "simulator";

interface Backend {
  name: string;
  provider: string;
  status: "online" | "offline" | "busy";
  qubits: number;
  queue: number;
  type: BackendType;
  topology: string;
  nativeOps: string[];
}

const backends: Backend[] = [
  { 
    name: "ibm_brisbane", 
    provider: "IBM Quantum", 
    status: "online", 
    qubits: 127, 
    queue: 12, 
    type: "superconductor",
    topology: "Heavy-Hex",
    nativeOps: ["CX", "ID", "RZ", "SX", "X"]
  },
  { 
    name: "ibm_sherbrooke", 
    provider: "IBM Quantum", 
    status: "busy", 
    qubits: 127, 
    queue: 45, 
    type: "superconductor",
    topology: "Heavy-Hex",
    nativeOps: ["CX", "ID", "RZ", "SX", "X"]
  },
  { 
    name: "Aquila", 
    provider: "QuEra (AWS Braket)", 
    status: "online", 
    qubits: 256, 
    queue: 3, 
    type: "neutral-atom",
    topology: "FPQA Reconfigurable",
    nativeOps: ["AOD Move", "Rydberg CZ", "Global"]
  },
  { 
    name: "Fresnel", 
    provider: "Pasqal", 
    status: "online", 
    qubits: 100, 
    queue: 8, 
    type: "neutral-atom",
    topology: "2D Grid (Movable)",
    nativeOps: ["AOD Move", "Rydberg", "Global"]
  },
  { 
    name: "Stim Simulator", 
    provider: "Local", 
    status: "online", 
    qubits: 1000, 
    queue: 0, 
    type: "simulator",
    topology: "All-to-All",
    nativeOps: ["Stabilizer Gates"]
  },
];

const typeIcons: Record<BackendType, React.ElementType> = {
  "superconductor": Cloud,
  "neutral-atom": Atom,
  "simulator": Cpu,
};

const typeLabels: Record<BackendType, string> = {
  "superconductor": "Superconductor",
  "neutral-atom": "Átomos Neutros",
  "simulator": "Simulador",
};

export function BackendStatus() {
  return (
    <div className="quantum-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Backends Agnósticos</h3>
        <span className="text-xs font-mono text-muted-foreground px-2 py-1 rounded bg-muted/50">
          Middle Layer v2.0
        </span>
      </div>
      
      <div className="space-y-3">
        {backends.map((backend) => {
          const Icon = typeIcons[backend.type];
          return (
            <div 
              key={backend.name}
              className="flex items-center gap-4 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer group"
            >
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center relative",
                backend.status === "online" && "bg-success/10",
                backend.status === "busy" && "bg-warning/10",
                backend.status === "offline" && "bg-destructive/10"
              )}>
                <Icon className={cn(
                  "w-5 h-5",
                  backend.status === "online" && "text-success",
                  backend.status === "busy" && "text-warning",
                  backend.status === "offline" && "text-destructive"
                )} />
                {/* Type badge */}
                {backend.type === "neutral-atom" && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-quantum-purple flex items-center justify-center">
                    <Zap className="w-2.5 h-2.5 text-white" />
                  </span>
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-medium truncate">{backend.name}</span>
                  {backend.status === "online" && <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />}
                  {backend.status === "busy" && <Clock className="w-4 h-4 text-warning flex-shrink-0" />}
                  {backend.status === "offline" && <XCircle className="w-4 h-4 text-destructive flex-shrink-0" />}
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{backend.provider}</span>
                  <span className="text-border">•</span>
                  <span className={cn(
                    "px-1.5 py-0.5 rounded text-[10px] font-medium",
                    backend.type === "neutral-atom" && "bg-quantum-purple/20 text-quantum-purple",
                    backend.type === "superconductor" && "bg-primary/20 text-primary",
                    backend.type === "simulator" && "bg-muted text-muted-foreground"
                  )}>
                    {typeLabels[backend.type]}
                  </span>
                </div>
              </div>

              <div className="text-right hidden group-hover:block">
                <p className="text-xs font-mono text-muted-foreground">{backend.topology}</p>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-mono">{backend.qubits}q</p>
                <p className="text-xs text-muted-foreground">Cola: {backend.queue}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Cloud className="w-3 h-3" /> SWAP-based
          </span>
          <span className="flex items-center gap-1">
            <Atom className="w-3 h-3 text-quantum-purple" /> AOD Movement
          </span>
        </div>
        <span className="font-mono">5 backends</span>
      </div>
    </div>
  );
}
