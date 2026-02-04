import { Cpu, Database, Shield, Lock, Layers, Atom, GitBranch } from "lucide-react";
import { ModuleCard } from "./ModuleCard";
import { AgentPanel } from "./AgentPanel";
import { CircuitUploader } from "./CircuitUploader";
import { MetricsChart } from "./MetricsChart";
import { BackendStatus } from "./BackendStatus";
import { ArchitectureDiagram } from "./ArchitectureDiagram";

interface DashboardProps {
  onNavigate: (module: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Architecture Banner */}
      <div className="quantum-card p-4 bg-gradient-to-r from-primary/5 via-quantum-purple/5 to-success/5 border-primary/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
              <Layers className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold quantum-text">Quantum Middle Layer v2.0</h2>
              <p className="text-sm text-muted-foreground">
                Arquitectura agnóstica HPC-inspired • No reimplementamos algoritmos, los orquestamos
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">Drivers:</span>
              <span className="font-mono text-primary">Qiskit</span>
              <span className="text-muted-foreground">•</span>
              <span className="font-mono text-quantum-purple">Pulser</span>
              <span className="text-muted-foreground">•</span>
              <span className="font-mono text-success">Cirq</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-5 gap-4">
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold quantum-text">1,247</p>
          <p className="text-sm text-muted-foreground mt-1">Circuitos orquestados</p>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-success">32.4%</p>
          <p className="text-sm text-muted-foreground mt-1">Reducción promedio</p>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-quantum-purple">100+</p>
          <p className="text-sm text-muted-foreground mt-1">Inst. paralelas/job</p>
        </div>
        <div className="quantum-card p-5 flex items-center gap-3">
          <Atom className="w-8 h-8 text-quantum-purple" />
          <div>
            <p className="text-xl font-mono font-bold">FPQA</p>
            <p className="text-xs text-muted-foreground">Átomos soportados</p>
          </div>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-warning">0</p>
          <p className="text-sm text-muted-foreground mt-1">Errores críticos</p>
        </div>
      </div>

      {/* Module Cards */}
      <div className="grid grid-cols-2 gap-6">
        <ModuleCard
          title="Orquestación de Routing"
          description="Paralelización de SabreLayout (Qiskit Rust) + Movimiento AOD (FPQA)"
          icon={Cpu}
          status="active"
          metrics={[
            { label: "Jobs hoy", value: "47" },
            { label: "Mejor reducción", value: "45%" },
            { label: "Backends", value: "5" },
          ]}
          onClick={() => onNavigate("routing")}
        />
        <ModuleCard
          title="Carga de Datos (QML)"
          description="ATP con optimización L-BFGS-B para umbral dinámico"
          icon={Database}
          status="idle"
          metrics={[
            { label: "Modelos", value: "12" },
            { label: "Precisión", value: "94%" },
            { label: "Qubits ahorrados", value: "45%" },
          ]}
          onClick={() => onNavigate("qml")}
        />
        <ModuleCard
          title="Simulación QEC (Stim)"
          description="Stim + PyMatching para Surface Codes. Re-ponderación DGR."
          icon={Shield}
          status="warning"
          metrics={[
            { label: "Simulaciones", value: "23" },
            { label: "Tasa error", value: "0.1%" },
            { label: "Latencia", value: "2.3ms" },
          ]}
          onClick={() => onNavigate("qec")}
        />
        <ModuleCard
          title="Sandbox PQC"
          description="Híbrida ECDH + ML-KEM (Kyber) via liboqs"
          icon={Lock}
          status="idle"
          metrics={[
            { label: "Handshakes", value: "156" },
            { label: "Latencia extra", value: "+12ms" },
            { label: "Tamaño paquete", value: "+1.2KB" },
          ]}
          onClick={() => onNavigate("pqc")}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <CircuitUploader />
          <MetricsChart />
        </div>
        <div className="space-y-6">
          <ArchitectureDiagram onNavigate={onNavigate} />
          <AgentPanel />
          <BackendStatus />
        </div>
      </div>
    </div>
  );
}
