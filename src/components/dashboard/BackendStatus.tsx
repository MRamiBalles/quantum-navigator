import { Server, Cloud, Cpu, CheckCircle, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface Backend {
  name: string;
  provider: string;
  status: "online" | "offline" | "busy";
  qubits: number;
  queue: number;
  icon: React.ElementType;
}

const backends: Backend[] = [
  { name: "ibm_brisbane", provider: "IBM Quantum", status: "online", qubits: 127, queue: 12, icon: Cloud },
  { name: "ibm_sherbrooke", provider: "IBM Quantum", status: "busy", qubits: 127, queue: 45, icon: Cloud },
  { name: "Aquila", provider: "AWS Braket", status: "online", qubits: 256, queue: 3, icon: Server },
  { name: "Simulator", provider: "Local", status: "online", qubits: 50, queue: 0, icon: Cpu },
];

export function BackendStatus() {
  return (
    <div className="quantum-card p-6">
      <h3 className="text-lg font-semibold mb-4">Backends Disponibles</h3>
      
      <div className="space-y-3">
        {backends.map((backend) => {
          const Icon = backend.icon;
          return (
            <div 
              key={backend.name}
              className="flex items-center gap-4 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer"
            >
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
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
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-medium">{backend.name}</span>
                  {backend.status === "online" && <CheckCircle className="w-4 h-4 text-success" />}
                  {backend.status === "busy" && <Clock className="w-4 h-4 text-warning" />}
                  {backend.status === "offline" && <XCircle className="w-4 h-4 text-destructive" />}
                </div>
                <span className="text-xs text-muted-foreground">{backend.provider}</span>
              </div>

              <div className="text-right">
                <p className="text-sm font-mono">{backend.qubits}q</p>
                <p className="text-xs text-muted-foreground">Cola: {backend.queue}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
