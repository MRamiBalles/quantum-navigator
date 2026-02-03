import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { QuantumBackground } from "@/components/background/QuantumBackground";
import { NeutralAtomStudio } from "@/components/neutral-atom";
import { BenchmarkResults } from "@/components/benchmarks";
import { NeuralDecoderAnalysis } from "@/components/benchmarks/NeuralDecoderAnalysis";

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

const Index = () => {
  const [activeModule, setActiveModule] = useState("dashboard");

  const renderModule = () => {
    switch (activeModule) {
      case "dashboard":
        return <Dashboard onNavigate={setActiveModule} />;
      case "neutral-atom":
        return <NeutralAtomStudio />;
      case "benchmarks":
        return <BenchmarkResults />;
      case "gnn-decoder":
        return <NeuralDecoderAnalysis />;
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
