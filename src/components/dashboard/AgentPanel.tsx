import { Brain, MessageSquare, Zap, Clock } from "lucide-react";

interface Message {
  role: "agent" | "system";
  content: string;
  timestamp: string;
}

const recentMessages: Message[] = [
  {
    role: "agent",
    content: "Circuito QAOA detectado. Activando optimizaciones de simetría de grafo...",
    timestamp: "12:45:32"
  },
  {
    role: "system",
    content: "LightSABRE completado: reducción del 28% en profundidad de circuito.",
    timestamp: "12:45:35"
  },
  {
    role: "agent",
    content: "Recomendación: Considerar ATP para el módulo QML con umbral τ=0.15",
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
            <h3 className="font-semibold">Agente IA</h3>
            <p className="text-xs text-muted-foreground font-mono">Gemini 1.5 Pro</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Zap className="w-3 h-3" />
          <span className="font-mono">128k tokens</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-primary">47</p>
          <p className="text-xs text-muted-foreground">Análisis hoy</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-success">98%</p>
          <p className="text-xs text-muted-foreground">Precisión</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-muted/50">
          <p className="text-xl font-mono font-semibold text-quantum-purple">1.2s</p>
          <p className="text-xs text-muted-foreground">Latencia</p>
        </div>
      </div>

      {/* Activity Log */}
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Actividad Reciente</span>
        </div>
        
        <div className="space-y-3 overflow-y-auto max-h-64">
          {recentMessages.map((msg, index) => (
            <div 
              key={index}
              className="p-3 rounded-lg bg-muted/30 border border-border/50"
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.role === "agent" ? (
                  <Brain className="w-3 h-3 text-primary" />
                ) : (
                  <Zap className="w-3 h-3 text-success" />
                )}
                <span className="text-xs font-mono text-muted-foreground flex items-center gap-1">
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
      <div className="mt-4 pt-4 border-t border-border">
        <button className="w-full py-2.5 px-4 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors">
          Iniciar Nuevo Análisis
        </button>
      </div>
    </div>
  );
}
