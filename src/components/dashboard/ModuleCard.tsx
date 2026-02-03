import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModuleCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  status: "active" | "idle" | "warning" | "error";
  metrics: {
    label: string;
    value: string;
    trend?: "up" | "down";
  }[];
  onClick?: () => void;
}

export function ModuleCard({ title, description, icon: Icon, status, metrics, onClick }: ModuleCardProps) {
  const statusConfig = {
    active: { label: "Activo", class: "status-active" },
    idle: { label: "Inactivo", class: "status-idle" },
    warning: { label: "Advertencia", class: "status-warning" },
    error: { label: "Error", class: "status-error" },
  };

  return (
    <div 
      onClick={onClick}
      className="quantum-card p-6 cursor-pointer group transition-all duration-300 hover:scale-[1.02]"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300",
            status === "active" && "bg-primary/10 group-hover:bg-primary/20",
            status === "warning" && "bg-warning/10",
            status === "idle" && "bg-muted",
            status === "error" && "bg-destructive/10"
          )}>
            <Icon className={cn(
              "w-6 h-6",
              status === "active" && "text-primary",
              status === "warning" && "text-warning",
              status === "idle" && "text-muted-foreground",
              status === "error" && "text-destructive"
            )} />
          </div>
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        
        <span className={cn(
          "px-2.5 py-1 rounded-full text-xs font-medium border",
          statusConfig[status].class
        )}>
          {statusConfig[status].label}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
        {metrics.map((metric, index) => (
          <div key={index} className="text-center">
            <p className="text-2xl font-mono font-semibold text-foreground">
              {metric.value}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{metric.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
