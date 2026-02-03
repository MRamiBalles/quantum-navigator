import { useState, useCallback, useRef, useEffect } from "react";
import { Atom, Plus, Trash2, Eye, EyeOff, Move, Check, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// =============================================================================
// TYPES
// =============================================================================

export type TrapRole = "SLM" | "AOD" | "STORAGE";

export interface AtomPosition {
  id: number;
  x: number;  // micrometers
  y: number;  // micrometers
  role: TrapRole;
  aod_row?: number;
  aod_col?: number;
}

export interface RegisterConfig {
  layoutType: "triangular" | "rectangular" | "honeycomb" | "arbitrary";
  minAtomDistance: number;  // micrometers
  blockadeRadius: number;   // micrometers
  atoms: AtomPosition[];
}

export interface ValidationError {
  type: "collision" | "blockade" | "bounds";
  atomIds: number[];
  message: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 400;
const SCALE = 12;  // pixels per micrometer
const GRID_STEP = 5;  // micrometer grid spacing
const MIN_DISTANCE_DEFAULT = 4.0;  // µm
const BLOCKADE_RADIUS_DEFAULT = 8.0;  // µm

const ROLE_COLORS: Record<TrapRole, { fill: string; stroke: string; label: string }> = {
  SLM: { fill: "#3b82f6", stroke: "#1d4ed8", label: "Data (SLM)" },
  AOD: { fill: "#f59e0b", stroke: "#d97706", label: "Shuttle (AOD)" },
  STORAGE: { fill: "#6b7280", stroke: "#4b5563", label: "Storage" },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function worldToCanvas(x: number, y: number): { cx: number; cy: number } {
  return {
    cx: CANVAS_WIDTH / 2 + x * SCALE,
    cy: CANVAS_HEIGHT / 2 - y * SCALE,  // Flip Y for canvas coords
  };
}

function canvasToWorld(cx: number, cy: number): { x: number; y: number } {
  return {
    x: (cx - CANVAS_WIDTH / 2) / SCALE,
    y: (CANVAS_HEIGHT / 2 - cy) / SCALE,
  };
}

function distance(a: AtomPosition, b: AtomPosition): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

function validateRegister(config: RegisterConfig): ValidationError[] {
  const errors: ValidationError[] = [];
  const { atoms, minAtomDistance } = config;

  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      const d = distance(atoms[i], atoms[j]);
      if (d < minAtomDistance) {
        errors.push({
          type: "collision",
          atomIds: [atoms[i].id, atoms[j].id],
          message: `Atoms ${atoms[i].id} and ${atoms[j].id} are ${d.toFixed(1)} µm apart (min: ${minAtomDistance} µm)`,
        });
      }
    }
  }

  return errors;
}

function findInteractions(atoms: AtomPosition[], blockadeRadius: number): [number, number][] {
  const pairs: [number, number][] = [];
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      if (distance(atoms[i], atoms[j]) <= blockadeRadius) {
        pairs.push([atoms[i].id, atoms[j].id]);
      }
    }
  }
  return pairs;
}

// =============================================================================
// ATOM REGISTER EDITOR COMPONENT
// =============================================================================

interface AtomRegisterEditorProps {
  initialConfig?: RegisterConfig;
  onChange?: (config: RegisterConfig) => void;
  readOnly?: boolean;
}

export function AtomRegisterEditor({
  initialConfig,
  onChange,
  readOnly = false,
}: AtomRegisterEditorProps) {
  // State
  const [config, setConfig] = useState<RegisterConfig>(initialConfig ?? {
    layoutType: "arbitrary",
    minAtomDistance: MIN_DISTANCE_DEFAULT,
    blockadeRadius: BLOCKADE_RADIUS_DEFAULT,
    atoms: [],
  });
  
  const [selectedAtom, setSelectedAtom] = useState<number | null>(null);
  const [showBlockade, setShowBlockade] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [currentTool, setCurrentTool] = useState<"select" | "add-slm" | "add-aod">("select");
  const [isDragging, setIsDragging] = useState(false);
  
  const canvasRef = useRef<SVGSVGElement>(null);

  // Derived state
  const errors = validateRegister(config);
  const interactions = findInteractions(config.atoms, config.blockadeRadius);
  const errorAtomIds = new Set(errors.flatMap(e => e.atomIds));

  // Update parent on change
  useEffect(() => {
    onChange?.(config);
  }, [config, onChange]);

  // Handlers
  const handleCanvasClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (readOnly) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const { x, y } = canvasToWorld(cx, cy);
    
    if (currentTool === "add-slm" || currentTool === "add-aod") {
      const role: TrapRole = currentTool === "add-slm" ? "SLM" : "AOD";
      const newId = config.atoms.length > 0 
        ? Math.max(...config.atoms.map(a => a.id)) + 1 
        : 0;
      
      // Snap to grid
      const snappedX = Math.round(x / GRID_STEP) * GRID_STEP;
      const snappedY = Math.round(y / GRID_STEP) * GRID_STEP;
      
      const newAtom: AtomPosition = {
        id: newId,
        x: snappedX,
        y: snappedY,
        role,
        ...(role === "AOD" ? { aod_row: 0, aod_col: config.atoms.filter(a => a.role === "AOD").length } : {}),
      };
      
      setConfig(prev => ({
        ...prev,
        atoms: [...prev.atoms, newAtom],
      }));
      setSelectedAtom(newId);
    } else {
      // Select mode - clicking empty space deselects
      setSelectedAtom(null);
    }
  }, [currentTool, config.atoms, readOnly]);

  const handleAtomClick = useCallback((e: React.MouseEvent, atomId: number) => {
    e.stopPropagation();
    setSelectedAtom(prev => prev === atomId ? null : atomId);
  }, []);

  const handleAtomDrag = useCallback((atomId: number, dx: number, dy: number) => {
    if (readOnly) return;
    
    setConfig(prev => ({
      ...prev,
      atoms: prev.atoms.map(a => 
        a.id === atomId 
          ? { ...a, x: a.x + dx / SCALE, y: a.y - dy / SCALE }
          : a
      ),
    }));
  }, [readOnly]);

  const handleDeleteSelected = useCallback(() => {
    if (selectedAtom === null || readOnly) return;
    
    setConfig(prev => ({
      ...prev,
      atoms: prev.atoms.filter(a => a.id !== selectedAtom),
    }));
    setSelectedAtom(null);
  }, [selectedAtom, readOnly]);

  const handleClearAll = useCallback(() => {
    if (readOnly) return;
    setConfig(prev => ({ ...prev, atoms: [] }));
    setSelectedAtom(null);
  }, [readOnly]);

  const handleBlockadeRadiusChange = useCallback((value: number[]) => {
    setConfig(prev => ({ ...prev, blockadeRadius: value[0] }));
  }, []);

  const handleMinDistanceChange = useCallback((value: number[]) => {
    setConfig(prev => ({ ...prev, minAtomDistance: value[0] }));
  }, []);

  // Render grid lines
  const renderGrid = () => {
    if (!showGrid) return null;
    
    const lines = [];
    const gridSpacingPx = GRID_STEP * SCALE;
    
    // Vertical lines
    for (let x = gridSpacingPx; x < CANVAS_WIDTH; x += gridSpacingPx) {
      lines.push(
        <line
          key={`v-${x}`}
          x1={x}
          y1={0}
          x2={x}
          y2={CANVAS_HEIGHT}
          className="stroke-muted/20"
          strokeWidth={1}
        />
      );
    }
    
    // Horizontal lines
    for (let y = gridSpacingPx; y < CANVAS_HEIGHT; y += gridSpacingPx) {
      lines.push(
        <line
          key={`h-${y}`}
          x1={0}
          y1={y}
          x2={CANVAS_WIDTH}
          y2={y}
          className="stroke-muted/20"
          strokeWidth={1}
        />
      );
    }
    
    // Center axes
    lines.push(
      <line
        key="axis-x"
        x1={0}
        y1={CANVAS_HEIGHT / 2}
        x2={CANVAS_WIDTH}
        y2={CANVAS_HEIGHT / 2}
        className="stroke-muted/40"
        strokeWidth={1}
        strokeDasharray="4 2"
      />,
      <line
        key="axis-y"
        x1={CANVAS_WIDTH / 2}
        y1={0}
        x2={CANVAS_WIDTH / 2}
        y2={CANVAS_HEIGHT}
        className="stroke-muted/40"
        strokeWidth={1}
        strokeDasharray="4 2"
      />
    );
    
    return <g className="pointer-events-none">{lines}</g>;
  };

  // Render blockade radii
  const renderBlockadeRadii = () => {
    if (!showBlockade) return null;
    
    return config.atoms.map(atom => {
      const { cx, cy } = worldToCanvas(atom.x, atom.y);
      const radiusPx = config.blockadeRadius * SCALE;
      
      return (
        <circle
          key={`blockade-${atom.id}`}
          cx={cx}
          cy={cy}
          r={radiusPx}
          className="fill-quantum-purple/5 stroke-quantum-purple/30"
          strokeWidth={1}
          strokeDasharray="4 2"
        />
      );
    });
  };

  // Render interaction lines
  const renderInteractions = () => {
    if (!showBlockade) return null;
    
    return interactions.map(([id1, id2]) => {
      const a1 = config.atoms.find(a => a.id === id1);
      const a2 = config.atoms.find(a => a.id === id2);
      if (!a1 || !a2) return null;
      
      const p1 = worldToCanvas(a1.x, a1.y);
      const p2 = worldToCanvas(a2.x, a2.y);
      
      return (
        <line
          key={`interaction-${id1}-${id2}`}
          x1={p1.cx}
          y1={p1.cy}
          x2={p2.cx}
          y2={p2.cy}
          className="stroke-quantum-purple/60"
          strokeWidth={2}
        />
      );
    });
  };

  // Render atoms
  const renderAtoms = () => {
    return config.atoms.map(atom => {
      const { cx, cy } = worldToCanvas(atom.x, atom.y);
      const roleStyle = ROLE_COLORS[atom.role];
      const isSelected = selectedAtom === atom.id;
      const hasError = errorAtomIds.has(atom.id);
      
      return (
        <g
          key={`atom-${atom.id}`}
          transform={`translate(${cx}, ${cy})`}
          className={cn(
            "cursor-pointer transition-transform",
            isSelected && "scale-125"
          )}
          onClick={(e) => handleAtomClick(e, atom.id)}
        >
          {/* Error indicator */}
          {hasError && (
            <circle
              r={18}
              className="fill-destructive/20 stroke-destructive"
              strokeWidth={2}
            />
          )}
          
          {/* Selection ring */}
          {isSelected && (
            <circle
              r={14}
              fill="none"
              className="stroke-primary"
              strokeWidth={2}
              strokeDasharray="4 2"
            />
          )}
          
          {/* Atom body */}
          <circle
            r={10}
            fill={roleStyle.fill}
            stroke={isSelected ? "#fff" : roleStyle.stroke}
            strokeWidth={2}
          />
          
          {/* AOD indicator */}
          {atom.role === "AOD" && (
            <Move className="w-3 h-3 text-white" style={{ transform: "translate(-6px, -6px)" }} />
          )}
          
          {/* ID label */}
          <text
            y={4}
            textAnchor="middle"
            className="fill-white text-xs font-bold pointer-events-none"
          >
            {atom.id}
          </text>
        </g>
      );
    });
  };

  return (
    <div className="quantum-card p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-quantum-purple/10 flex items-center justify-center">
            <Atom className="w-5 h-5 text-quantum-purple" />
          </div>
          <div>
            <h3 className="font-semibold">Neutral Atom Register Editor</h3>
            <p className="text-sm text-muted-foreground">
              Define la geometría del registro • {config.atoms.length} átomos
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {errors.length > 0 && (
            <Badge variant="destructive" className="gap-1">
              <AlertTriangle className="w-3 h-3" />
              {errors.length} {errors.length === 1 ? "error" : "errores"}
            </Badge>
          )}
          <Badge variant="outline" className="gap-1">
            <Check className="w-3 h-3 text-success" />
            {interactions.length} interacciones
          </Badge>
        </div>
      </div>

      {/* Toolbar */}
      {!readOnly && (
        <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant={currentTool === "select" ? "default" : "ghost"}
              onClick={() => setCurrentTool("select")}
            >
              <Move className="w-4 h-4 mr-1" />
              Seleccionar
            </Button>
            <Button
              size="sm"
              variant={currentTool === "add-slm" ? "default" : "ghost"}
              onClick={() => setCurrentTool("add-slm")}
              className={currentTool === "add-slm" ? "bg-blue-600" : ""}
            >
              <Plus className="w-4 h-4 mr-1" />
              SLM
            </Button>
            <Button
              size="sm"
              variant={currentTool === "add-aod" ? "default" : "ghost"}
              onClick={() => setCurrentTool("add-aod")}
              className={currentTool === "add-aod" ? "bg-amber-600" : ""}
            >
              <Plus className="w-4 h-4 mr-1" />
              AOD
            </Button>
          </div>
          
          <div className="h-6 w-px bg-border" />
          
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDeleteSelected}
            disabled={selectedAtom === null}
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Eliminar
          </Button>
          
          <Button
            size="sm"
            variant="ghost"
            onClick={handleClearAll}
            disabled={config.atoms.length === 0}
          >
            Limpiar todo
          </Button>
        </div>
      )}

      {/* Canvas */}
      <div className="relative border border-border rounded-lg overflow-hidden bg-card">
        <svg
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          className={cn(
            "w-full h-auto",
            currentTool !== "select" && "cursor-crosshair"
          )}
          onClick={handleCanvasClick}
        >
          {/* Background */}
          <rect width="100%" height="100%" className="fill-background" />
          
          {/* Grid */}
          {renderGrid()}
          
          {/* Blockade radii (behind atoms) */}
          {renderBlockadeRadii()}
          
          {/* Interaction lines */}
          {renderInteractions()}
          
          {/* Atoms */}
          {renderAtoms()}
          
          {/* Scale indicator */}
          <g transform={`translate(${CANVAS_WIDTH - 80}, ${CANVAS_HEIGHT - 20})`}>
            <line x1={0} y1={0} x2={5 * SCALE} y2={0} className="stroke-muted-foreground" strokeWidth={2} />
            <line x1={0} y1={-3} x2={0} y2={3} className="stroke-muted-foreground" strokeWidth={2} />
            <line x1={5 * SCALE} y1={-3} x2={5 * SCALE} y2={3} className="stroke-muted-foreground" strokeWidth={2} />
            <text x={5 * SCALE / 2} y={-8} textAnchor="middle" className="fill-muted-foreground text-xs">
              5 µm
            </text>
          </g>
        </svg>

        {/* Empty state */}
        {config.atoms.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <p className="text-muted-foreground">
              Usa las herramientas SLM/AOD para añadir átomos
            </p>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left: View controls */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium flex items-center gap-2">
              {showBlockade ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              Mostrar Radio de Bloqueo
            </label>
            <Switch
              checked={showBlockade}
              onCheckedChange={setShowBlockade}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Mostrar Grid</label>
            <Switch
              checked={showGrid}
              onCheckedChange={setShowGrid}
            />
          </div>
        </div>
        
        {/* Right: Physics parameters */}
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Radio de Bloqueo (R<sub>b</sub>)</label>
              <span className="text-sm font-mono text-quantum-purple">
                {config.blockadeRadius.toFixed(1)} µm
              </span>
            </div>
            <Slider
              value={[config.blockadeRadius]}
              onValueChange={handleBlockadeRadiusChange}
              min={4}
              max={15}
              step={0.5}
              disabled={readOnly}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Distancia Mínima</label>
              <span className="text-sm font-mono">
                {config.minAtomDistance.toFixed(1)} µm
              </span>
            </div>
            <Slider
              value={[config.minAtomDistance]}
              onValueChange={handleMinDistanceChange}
              min={2}
              max={10}
              step={0.5}
              disabled={readOnly}
            />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 pt-2 border-t border-border text-sm">
        {Object.entries(ROLE_COLORS).map(([role, style]) => (
          <div key={role} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: style.fill, border: `2px solid ${style.stroke}` }}
            />
            <span className="text-muted-foreground">{style.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-quantum-purple/60" />
          <span className="text-muted-foreground">Interacción Rydberg</span>
        </div>
      </div>

      {/* Error list */}
      {errors.length > 0 && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 space-y-1">
          <p className="text-sm font-medium text-destructive flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Errores de Validación
          </p>
          <ul className="text-sm text-destructive/80 list-disc list-inside">
            {errors.map((err, i) => (
              <li key={i}>{err.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Selected atom info */}
      {selectedAtom !== null && (
        <div className="p-3 rounded-lg bg-muted/30 flex items-center justify-between">
          <div className="text-sm">
            <span className="font-medium">Átomo {selectedAtom}</span>
            {(() => {
              const atom = config.atoms.find(a => a.id === selectedAtom);
              if (!atom) return null;
              return (
                <span className="text-muted-foreground ml-2">
                  ({atom.x.toFixed(1)}, {atom.y.toFixed(1)}) µm • {ROLE_COLORS[atom.role].label}
                </span>
              );
            })()}
          </div>
          <Badge variant="outline">{config.atoms.find(a => a.id === selectedAtom)?.role}</Badge>
        </div>
      )}
    </div>
  );
}

export default AtomRegisterEditor;
