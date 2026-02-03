import { useState } from "react";
import { Upload, FileCode, CheckCircle, AlertCircle, Atom, Cloud, Cpu, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

type BackendType = "superconductor" | "neutral-atom" | "auto";

interface CircuitInfo {
  name: string;
  qubits: number;
  depth: number;
  gates: number;
  type: "QAOA" | "VQE" | "QFT" | "Grover" | "Custom";
}

interface OptimizationStrategy {
  backend: BackendType;
  strategy: string;
  description: string;
  estimatedReduction: string;
}

export function CircuitUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedCircuit, setUploadedCircuit] = useState<CircuitInfo | null>(null);
  const [selectedBackend, setSelectedBackend] = useState<BackendType>("auto");

  // Simulated circuit detection
  const handleUpload = () => {
    setUploadedCircuit({
      name: "portfolio_qaoa.qasm",
      qubits: 32,
      depth: 156,
      gates: 892,
      type: "QAOA",
    });
  };

  const strategies: Record<BackendType, OptimizationStrategy> = {
    superconductor: {
      backend: "superconductor",
      strategy: "Orquestación SabreLayout Paralela",
      description: "100+ instancias con diferentes semillas (lookahead/decay). Usa Qiskit Rust nativo.",
      estimatedReduction: "25-32%",
    },
    "neutral-atom": {
      backend: "neutral-atom",
      strategy: "Movimiento AOD + Ancilas Voladoras",
      description: "Compilación FPQA-C con reconfiguración dinámica. Sin cadenas de SWAP.",
      estimatedReduction: "40-55%",
    },
    auto: {
      backend: "auto",
      strategy: "Selección Automática por Topología",
      description: "El agente analiza el circuito y selecciona la mejor estrategia backend.",
      estimatedReduction: "30-45%",
    },
  };

  const currentStrategy = strategies[selectedBackend];

  return (
    <div className="quantum-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Subir Circuito</h3>
        <div className="flex items-center gap-1 text-xs">
          <Layers className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground font-mono">Middle Layer</span>
        </div>
      </div>
      
      {!uploadedCircuit ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleUpload(); }}
          onClick={handleUpload}
          className={cn(
            "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300",
            isDragging 
              ? "border-primary bg-primary/5" 
              : "border-border hover:border-primary/50 hover:bg-muted/30"
          )}
        >
          <div className="flex flex-col items-center gap-4">
            <div className={cn(
              "w-14 h-14 rounded-xl flex items-center justify-center transition-colors",
              isDragging ? "bg-primary/20" : "bg-muted"
            )}>
              <Upload className={cn(
                "w-7 h-7 transition-colors",
                isDragging ? "text-primary" : "text-muted-foreground"
              )} />
            </div>
            <div>
              <p className="font-medium mb-1">
                {isDragging ? "Suelta el archivo aquí" : "Arrastra tu circuito"}
              </p>
              <p className="text-sm text-muted-foreground">
                Soporta .qasm, .py (Qiskit/Cirq/Pulser), .json (Descriptor Agnóstico)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* File info */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 border border-border">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileCode className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1">
              <p className="font-medium font-mono">{uploadedCircuit.name}</p>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle className="w-4 h-4 text-success" />
                <span className="text-sm text-success">Circuito válido • Descriptor JSON generado</span>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full bg-secondary/20 text-secondary text-sm font-medium">
              {uploadedCircuit.type}
            </span>
          </div>

          {/* Circuit metrics */}
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-muted/30 text-center">
              <p className="text-xl font-mono font-semibold">{uploadedCircuit.qubits}</p>
              <p className="text-xs text-muted-foreground">Qubits</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 text-center">
              <p className="text-xl font-mono font-semibold">{uploadedCircuit.depth}</p>
              <p className="text-xs text-muted-foreground">Profundidad</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 text-center">
              <p className="text-xl font-mono font-semibold">{uploadedCircuit.gates}</p>
              <p className="text-xs text-muted-foreground">Puertas</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 text-center">
              <p className="text-xl font-mono font-semibold text-warning">42</p>
              <p className="text-xs text-muted-foreground">2Q Gates</p>
            </div>
          </div>

          {/* Backend Selection - Hardware Agnostic */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Estrategia de Backend</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSelectedBackend("auto")}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all",
                  selectedBackend === "auto"
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Cpu className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">Auto</span>
                </div>
                <p className="text-[10px] text-muted-foreground">IA decide</p>
              </button>
              <button
                onClick={() => setSelectedBackend("superconductor")}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all",
                  selectedBackend === "superconductor"
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Cloud className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">SWAP</span>
                </div>
                <p className="text-[10px] text-muted-foreground">IBM/Rigetti</p>
              </button>
              <button
                onClick={() => setSelectedBackend("neutral-atom")}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all",
                  selectedBackend === "neutral-atom"
                    ? "border-quantum-purple bg-quantum-purple/10"
                    : "border-border hover:border-quantum-purple/50"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Atom className="w-4 h-4 text-quantum-purple" />
                  <span className="text-sm font-medium">AOD</span>
                </div>
                <p className="text-[10px] text-muted-foreground">QuEra/Pasqal</p>
              </button>
            </div>
          </div>

          {/* Agent recommendation */}
          <div className={cn(
            "flex items-start gap-3 p-4 rounded-lg border",
            selectedBackend === "neutral-atom" 
              ? "bg-quantum-purple/5 border-quantum-purple/20" 
              : "bg-primary/5 border-primary/20"
          )}>
            <AlertCircle className={cn(
              "w-5 h-5 mt-0.5",
              selectedBackend === "neutral-atom" ? "text-quantum-purple" : "text-primary"
            )} />
            <div>
              <p className={cn(
                "text-sm font-medium",
                selectedBackend === "neutral-atom" ? "text-quantum-purple" : "text-primary"
              )}>
                {currentStrategy.strategy}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {currentStrategy.description}
              </p>
              <p className="text-xs font-mono mt-2 text-success">
                Reducción estimada: {currentStrategy.estimatedReduction}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button className={cn(
              "flex-1 py-2.5 rounded-lg font-medium transition-colors",
              selectedBackend === "neutral-atom"
                ? "bg-quantum-purple text-white hover:bg-quantum-purple/90"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            )}>
              Orquestar Optimización
            </button>
            <button 
              onClick={() => setUploadedCircuit(null)}
              className="px-4 py-2.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              Cambiar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
