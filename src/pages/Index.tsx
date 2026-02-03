import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { QuantumBackground } from "@/components/background/QuantumBackground";

const moduleTitles: Record<string, string> = {
  dashboard: "Dashboard Principal",
  routing: "Compilación & Routing Inteligente",
  qml: "Carga de Datos (QML)",
  qec: "Corrección de Errores (QEC)",
  pqc: "Criptografía Post-Cuántica",
};

const Index = () => {
  const [activeModule, setActiveModule] = useState("dashboard");

  return (
    <div className="flex min-h-screen bg-background relative overflow-hidden">
      <QuantumBackground />
      
      <div className="relative z-10 flex flex-1">
        <Sidebar activeModule={activeModule} onModuleChange={setActiveModule} />
        
        <main className="flex-1 flex flex-col overflow-hidden">
          <Header title={moduleTitles[activeModule]} />
          
          <div className="flex-1 overflow-y-auto grid-pattern">
            {activeModule === "dashboard" && (
              <Dashboard onNavigate={setActiveModule} />
            )}
            
            {activeModule !== "dashboard" && (
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
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
