import { Brain, MessageSquare, Zap, Clock, Layers, GitBranch } from "lucide-react";

interface Message {
  role: "agent" | "system" | "middleware";
  content: string;
  timestamp: string;
}

const recentMessages: Message[] = [
  {
    role: "middleware",
    content: "Descriptor JSON generado → Traduciendo a Qiskit (Heavy-Hex) + Pulser (QuEra)",
    timestamp: "12:45:30"
  },
  {
    role: "agent",
    content: "Circuito QAOA detectado. Lanzando 100 instancias SabreLayout en paralelo (Rust)...",
    timestamp: "12:45:32"
  },
  {
    role: "system",
    content: "Mejor layout: semilla #47, decay=0.95. Reducción: 28% profundidad.",
    timestamp: "12:45:35"
  },
  {
    role: "agent",
    content: "Backend Aquila (FPQA) disponible. ¿Recompilar con movimiento de átomos? Reducción estimada: +15%",
    timestamp: "12:45:38"
  },
];

export function AgentPanel() {
  return (
    <div className="quantum-card p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center animate-pulse-glow">
              <Brain className="w-5 h-5 text-primary" />
            </div>
            <span className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full bg-success border-2 border-card" />
          </div>
          <div>
            <h3 className="font-semibold">Agente Orquestador</h3>
            <p className="text-xs text-muted-foreground font-mono">Gemini 2.5 Flash</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Zap className="w-3 h-3" />
          <span className="font-mono">1M tokens</span>
        </div>
      </div>

      {/* Architecture Badge */}
      <div className="flex items-center gap-2 mb-4 p-2 rounded-lg bg-muted/50 border border-border">
        <Layers className="w-4 h-4 text-quantum-purple" />
        <span className="text-xs font-medium">Middle Layer Agnóstico</span>
        <span className="ml-auto text-xs font-mono text-muted-foreground">v2.0</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-primary">47</p>
          <p className="text-xs text-muted-foreground">Orquestaciones</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-success">100+</p>
          <p className="text-xs text-muted-foreground">Inst. Paralelas</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-quantum-purple">3</p>
          <p className="text-xs text-muted-foreground">SDK Drivers</p>
        </div>
      </div>

      {/* Supported Drivers */}
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-4 h-4 text-muted-foreground" />
        <span className="text-xs font-medium">Drivers Activos:</span>
        <div className="flex gap-1">
          <span className="px-2 py-0.5 rounded bg-primary/20 text-primary text-[10px] font-mono">Qiskit</span>
          <span className="px-2 py-0.5 rounded bg-quantum-purple/20 text-quantum-purple text-[10px] font-mono">Pulser</span>
          <span className="px-2 py-0.5 rounded bg-success/20 text-success text-[10px] font-mono">Cirq</span>
        </div>
      </div>

      {/* Activity Log */}
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Pipeline de Orquestación</span>
        </div>
        
        <div className="space-y-3 overflow-y-auto max-h-64">
          {recentMessages.map((msg, index) => (
            <div 
              key={index}
              className="p-3 rounded-lg bg-muted/30 border border-border/50"
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.role === "agent" && <Brain className="w-3 h-3 text-primary" />}
                {msg.role === "system" && <Zap className="w-3 h-3 text-success" />}
                {msg.role === "middleware" && <Layers className="w-3 h-3 text-quantum-purple" />}
                <span className="text-[10px] font-mono text-muted-foreground uppercase">
                  {msg.role}
                </span>
                <span className="text-xs font-mono text-muted-foreground flex items-center gap-1 ml-auto">
                  <Clock className="w-3 h-3" />
                  {msg.timestamp}
                </span>
              </div>
              <p className="text-sm text-foreground/90">{msg.content}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-border space-y-2">
        <button className="w-full py-2.5 px-4 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors">
          Nueva Orquestación
        </button>
        <div className="flex gap-2">
          <button className="flex-1 py-2 px-3 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
            Ver Descriptores JSON
          </button>
          <button className="flex-1 py-2 px-3 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
            Comparar Backends
          </button>
        </div>
      </div>
    </div>
  );
}
