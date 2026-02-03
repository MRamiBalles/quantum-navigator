import { useState } from "react";
import {
  Cpu,
  Database,
  Shield,
  Lock,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Atom,
  Layers,
  BarChart3,
  FlaskConical,
  BrainCircuit
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  status: "active" | "idle" | "warning";
  badge?: string;
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: Activity, status: "active" },
  { id: "neutral-atom", label: "Neutral Atom Studio", icon: Atom, status: "active", badge: "FPQA" },
  { id: "benchmarks", label: "Benchmark Results", icon: BarChart3, status: "active", badge: "4" },
  { id: "gnn-decoder", label: "Neural Decoder", icon: BrainCircuit, status: "active", badge: "v6.3" },
  { id: "routing", label: "Orquestación Routing", icon: Cpu, status: "active", badge: "v2" },
  { id: "qml", label: "Carga de Datos (ATP)", icon: Database, status: "idle" },
  { id: "qec", label: "QEC (Stim)", icon: Shield, status: "warning" },
  { id: "pqc", label: "Sandbox PQC", icon: Lock, status: "idle" },
];

interface SidebarProps {
  activeModule: string;
  onModuleChange: (id: string) => void;
}

export function Sidebar({ activeModule, onModuleChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "relative flex flex-col h-screen border-r border-border bg-sidebar transition-all duration-300",
        collapsed ? "w-20" : "w-72"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 p-6 border-b border-border">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl overflow-hidden quantum-glow">
          <img src="/favicon.png" alt="Q-Orchestrator" className="w-full h-full object-cover" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-lg font-semibold quantum-text">Q-Orchestrator</span>
            <span className="text-xs text-muted-foreground font-mono">Middle Layer v2.0</span>
          </div>
        )}
      </div>

      {/* Architecture Badge */}
      {!collapsed && (
        <div className="mx-4 mt-4 p-3 rounded-lg bg-muted/50 border border-border">
          <div className="flex items-center gap-2 text-xs">
            <Layers className="w-4 h-4 text-quantum-purple" />
            <span className="font-medium">Arquitectura Agnóstica</span>
          </div>
          <p className="text-[10px] text-muted-foreground mt-1">
            Orquestación sobre Qiskit/Pulser/Cirq
          </p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeModule === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onModuleChange(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
                "hover:bg-sidebar-accent group",
                isActive && "bg-primary/10 border border-primary/30"
              )}
            >
              <div className="relative">
                <Icon
                  className={cn(
                    "w-5 h-5 transition-colors",
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                  )}
                />
                {/* Status indicator */}
                <span
                  className={cn(
                    "absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full",
                    item.status === "active" && "bg-success",
                    item.status === "warning" && "bg-warning",
                    item.status === "idle" && "bg-muted-foreground/50"
                  )}
                />
              </div>
              {!collapsed && (
                <div className="flex items-center gap-2 flex-1">
                  <span
                    className={cn(
                      "text-sm font-medium transition-colors",
                      isActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  >
                    {item.label}
                  </span>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-quantum-purple/20 text-quantum-purple">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Settings */}
      <div className="p-4 border-t border-border">
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-sidebar-accent transition-colors text-muted-foreground hover:text-foreground">
          <Settings className="w-5 h-5" />
          {!collapsed && <span className="text-sm font-medium">Configuración</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-card border border-border flex items-center justify-center hover:bg-muted transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-muted-foreground" />
        )}
      </button>
    </aside>
  );
}
