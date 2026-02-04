import { useState, lazy, Suspense } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { QuantumBackground } from "@/components/background/QuantumBackground";
import { Loader2 } from "lucide-react";

// Lazy load heavy components for better initial performance
const NeutralAtomStudio = lazy(() => 
  import("@/components/neutral-atom/NeutralAtomStudio").then(m => ({ default: m.NeutralAtomStudio }))
);
const BenchmarkResults = lazy(() => 
  import("@/components/benchmarks/BenchmarkResults").then(m => ({ default: m.BenchmarkResults }))
);
const NeuralDecoderAnalysis = lazy(() => 
  import("@/components/benchmarks/NeuralDecoderAnalysis").then(m => ({ default: m.NeuralDecoderAnalysis }))
);
const QMLResourceAnalysis = lazy(() => 
  import("@/components/benchmarks/QMLResourceAnalysis").then(m => ({ default: m.QMLResourceAnalysis }))
);
const CryptoResilience = lazy(() => 
  import("@/components/benchmarks/CryptoResilience").then(m => ({ default: m.CryptoResilience }))
);
const TopologyOptimizer = lazy(() => 
  import("@/components/benchmarks/TopologyOptimizer").then(m => ({ default: m.TopologyOptimizer }))
);

const moduleTitles: Record<string, string> = {
  dashboard: "Dashboard Principal",
  "neutral-atom": "Neutral Atom Studio",
  benchmarks: "Benchmark Results",
  "gnn-decoder": "Neural Decoder Analysis (GNN)",
  routing: "Orquestación de Routing (SWAP + AOD)",
  qml: "Carga de Datos ATP (L-BFGS-B)",
  qec: "Simulación QEC (Stim + PyMatching)",
  pqc: "Sandbox PQC (Kyber + liboqs)",
};

// Loading fallback component
const ModuleLoader = () => (
  <div className="flex items-center justify-center h-full min-h-[400px]">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
        <Loader2 className="w-6 h-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
      </div>
      <p className="text-sm text-muted-foreground animate-pulse">
        Cargando módulo...
      </p>
    </div>
  </div>
);

const Index = () => {
  const [activeModule, setActiveModule] = useState("dashboard");

  const renderModule = () => {
    switch (activeModule) {
      case "dashboard":
        // Dashboard loads immediately (critical path)
        return <Dashboard onNavigate={setActiveModule} />;
      case "neutral-atom":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <NeutralAtomStudio />
          </Suspense>
        );
      case "benchmarks":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <BenchmarkResults />
          </Suspense>
        );
      case "gnn-decoder":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <NeuralDecoderAnalysis />
          </Suspense>
        );
      case "qml":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <QMLResourceAnalysis />
          </Suspense>
        );
      case "pqc":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <CryptoResilience />
          </Suspense>
        );
      case "routing":
        return (
          <Suspense fallback={<ModuleLoader />}>
            <TopologyOptimizer />
          </Suspense>
        );
      default:
        return (
          <div className="p-8 animate-fade-in">
            <div className="quantum-card p-12 text-center">
              <h2 className="text-2xl font-semibold mb-4 quantum-text">
                {moduleTitles[activeModule]}
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto">
                Este módulo está en desarrollo. Aquí se implementará la funcionalidad
                completa para {moduleTitles[activeModule].toLowerCase()}.
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex min-h-screen bg-background relative overflow-hidden">
      <QuantumBackground />

      <div className="relative z-10 flex flex-1">
        <Sidebar activeModule={activeModule} onModuleChange={setActiveModule} />

        <main className="flex-1 flex flex-col overflow-hidden">
          <Header title={moduleTitles[activeModule]} />

          <div className="flex-1 overflow-y-auto grid-pattern">
            {renderModule()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
