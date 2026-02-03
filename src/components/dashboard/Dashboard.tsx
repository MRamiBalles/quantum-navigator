import { Cpu, Database, Shield, Lock } from "lucide-react";
import { ModuleCard } from "./ModuleCard";
import { AgentPanel } from "./AgentPanel";
import { CircuitUploader } from "./CircuitUploader";
import { MetricsChart } from "./MetricsChart";
import { BackendStatus } from "./BackendStatus";

interface DashboardProps {
  onNavigate: (module: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Hero Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold quantum-text">1,247</p>
          <p className="text-sm text-muted-foreground mt-1">Circuitos optimizados</p>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-success">32.4%</p>
          <p className="text-sm text-muted-foreground mt-1">Reducción promedio</p>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-quantum-purple">4</p>
          <p className="text-sm text-muted-foreground mt-1">Backends conectados</p>
        </div>
        <div className="quantum-card p-5">
          <p className="text-3xl font-mono font-bold text-warning">0</p>
          <p className="text-sm text-muted-foreground mt-1">Errores críticos</p>
        </div>
      </div>

      {/* Module Cards */}
      <div className="grid grid-cols-2 gap-6">
        <ModuleCard
          title="Compilación & Routing"
          description="LightSABRE para topologías complejas"
          icon={Cpu}
          status="active"
          metrics={[
            { label: "Circuitos hoy", value: "47" },
            { label: "Reducción media", value: "28%" },
            { label: "SWAPs evitados", value: "1.2k" },
          ]}
          onClick={() => onNavigate("routing")}
        />
        <ModuleCard
          title="Carga de Datos (QML)"
          description="ATP para evitar Barren Plateaus"
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
          title="Corrección de Errores"
          description="Simulación QEC con Stim"
          icon={Shield}
          status="warning"
          metrics={[
            { label: "Simulaciones", value: "23" },
            { label: "Tasa error", value: "0.1%" },
            { label: "Decodificación", value: "2.3ms" },
          ]}
          onClick={() => onNavigate("qec")}
        />
        <ModuleCard
          title="Criptografía PQC"
          description="Híbrida ECDH + ML-KEM (Kyber)"
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
          <AgentPanel />
          <BackendStatus />
        </div>
      </div>
    </div>
  );
}
