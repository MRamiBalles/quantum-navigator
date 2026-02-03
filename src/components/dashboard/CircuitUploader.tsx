import { useState } from "react";
import { Upload, FileCode, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface CircuitInfo {
  name: string;
  qubits: number;
  depth: number;
  gates: number;
  type: "QAOA" | "VQE" | "QFT" | "Grover" | "Custom";
}

export function CircuitUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedCircuit, setUploadedCircuit] = useState<CircuitInfo | null>(null);

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

  return (
    <div className="quantum-card p-6">
      <h3 className="text-lg font-semibold mb-4">Subir Circuito</h3>
      
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
                {isDragging ? "Suelta el archivo aquí" : "Arrastra tu circuito OpenQASM"}
              </p>
              <p className="text-sm text-muted-foreground">
                Soporta .qasm, .py (Qiskit), .json
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
                <span className="text-sm text-success">Circuito válido detectado</span>
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
              <p className="text-xl font-mono font-semibold">42</p>
              <p className="text-xs text-muted-foreground">SWAPs est.</p>
            </div>
          </div>

          {/* Agent recommendation */}
          <div className="flex items-start gap-3 p-4 rounded-lg bg-primary/5 border border-primary/20">
            <AlertCircle className="w-5 h-5 text-primary mt-0.5" />
            <div>
              <p className="text-sm font-medium text-primary">Recomendación del Agente</p>
              <p className="text-sm text-muted-foreground mt-1">
                Circuito QAOA detectado. Se recomienda usar LightSABRE con lookahead=3 
                para la topología Heavy-Hex de IBM. Reducción estimada: 25-30%.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button className="flex-1 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors">
              Optimizar Circuito
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
