# AtomRegisterEditor Component

## Frontend Technical Report - v2.1

**Autor**: Equipo de Desarrollo Frontend  
**Fecha**: 3 de Febrero de 2026  
**Framework**: React + TypeScript + SVG

---

## 1. Resumen Ejecutivo

El `AtomRegisterEditor` es el componente central para la visualización y edición interactiva de registros de átomos neutros. Proporciona una interfaz WYSIWYG (What You See Is What You Get) donde la geometría visible corresponde directamente a la física subyacente.

### Principio de Diseño

> "La geometría es el programa" — Los usuarios diseñan algoritmos cuánticos colocando átomos en el espacio, no escribiendo código abstracto.

---

## 2. Arquitectura del Componente

```
AtomRegisterEditor
├── Props
│   ├── initialConfig?: RegisterConfig
│   ├── onChange?: (config) => void
│   └── readOnly?: boolean
├── State
│   ├── config: RegisterConfig
│   ├── selectedAtom: number | null
│   ├── currentTool: "select" | "add-slm" | "add-aod"
│   └── showBlockade: boolean
└── Render
    ├── Toolbar
    ├── SVG Canvas
    │   ├── Grid
    │   ├── Zones (v2.1)
    │   ├── Blockade Radii
    │   ├── Interaction Lines
    │   └── Atoms
    ├── Controls Panel
    └── Error List
```

---

## 3. Sistema de Coordenadas

### 3.1 Transformación Mundo → Canvas

```typescript
const SCALE = 12;  // pixels per micrometer

function worldToCanvas(x: number, y: number) {
  return {
    cx: CANVAS_WIDTH / 2 + x * SCALE,
    cy: CANVAS_HEIGHT / 2 - y * SCALE,  // Y invertido
  };
}
```

**Dimensiones**:
- Canvas: 600 × 400 px
- Escala: 12 px/µm
- Rango efectivo: ±25 µm horizontalmente, ±17 µm verticalmente
- Grid: 5 µm spacing

### 3.2 Snap to Grid

Los átomos nuevos se alinean automáticamente al grid de 5 µm:

```typescript
const snappedX = Math.round(x / GRID_STEP) * GRID_STEP;
const snappedY = Math.round(y / GRID_STEP) * GRID_STEP;
```

---

## 4. Sistema de Roles de Átomo

| Rol | Color | Descripción | Indicador |
|-----|-------|-------------|-----------|
| SLM | 🔵 `#3b82f6` | Trampa estática | Círculo sólido |
| AOD | 🟠 `#f59e0b` | Trampa móvil | Círculo + icono Move |
| STORAGE | ⚫ `#6b7280` | Reserva | Círculo gris |

---

## 5. Sistema de Zonas (v2.1)

### 5.1 Colores de Zona

```typescript
const ZONE_COLORS: Record<ZoneType, ZoneStyle> = {
  STORAGE:      { fill: "rgba(99, 102, 241, 0.08)",  stroke: "#6366f1" },
  ENTANGLEMENT: { fill: "rgba(16, 185, 129, 0.08)",  stroke: "#10b981" },
  READOUT:      { fill: "rgba(245, 158, 11, 0.08)", stroke: "#f59e0b" },
  PREPARATION:  { fill: "rgba(6, 182, 212, 0.08)",  stroke: "#06b6d4" },
  RESERVOIR:    { fill: "rgba(55, 65, 81, 0.12)",   stroke: "#374151" },
  BUFFER:       { fill: "rgba(156, 163, 175, 0.05)", stroke: "#9ca3af" },
};
```

### 5.2 Rendering de Zonas

```typescript
const renderZones = () => {
  if (!config.zones) return null;
  
  return config.zones.map(zone => {
    const topLeft = worldToCanvas(zone.x_min, zone.y_max);
    const bottomRight = worldToCanvas(zone.x_max, zone.y_min);
    
    return (
      <g key={zone.zone_id}>
        <rect
          x={topLeft.cx}
          y={topLeft.cy}
          width={bottomRight.cx - topLeft.cx}
          height={bottomRight.cy - topLeft.cy}
          fill={ZONE_COLORS[zone.zone_type].fill}
          stroke={ZONE_COLORS[zone.zone_type].stroke}
        />
        <text>
          {zone.zone_type}
          {zone.shielding_light && " 🛡️"}
        </text>
      </g>
    );
  });
};
```

---

## 6. Visualización de Física

### 6.1 Radio de Bloqueo Rydberg

Cada átomo muestra un círculo semitransparente indicando su radio de bloqueo:

```typescript
<circle
  r={blockadeRadius * SCALE}
  className="fill-quantum-purple/5 stroke-quantum-purple/30"
  strokeDasharray="4 2"
/>
```

**Objetivo UX**: El usuario ve inmediatamente qué átomos pueden entrelazarse.

### 6.2 Líneas de Interacción

Átomos dentro del radio de bloqueo mutuo muestran una línea conectándolos:

```typescript
const findInteractions = (atoms, blockadeRadius) => {
  const pairs = [];
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      if (distance(atoms[i], atoms[j]) <= blockadeRadius) {
        pairs.push([atoms[i].id, atoms[j].id]);
      }
    }
  }
  return pairs;
};
```

---

## 7. Validación en Tiempo Real

### 7.1 Detección de Colisiones

```typescript
function validateRegister(config: RegisterConfig): ValidationError[] {
  const errors: ValidationError[] = [];
  
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      const d = distance(atoms[i], atoms[j]);
      if (d < config.minAtomDistance) {
        errors.push({
          type: "collision",
          atomIds: [atoms[i].id, atoms[j].id],
          message: `Atoms ${i} and ${j} are ${d.toFixed(1)} µm apart`,
        });
      }
    }
  }
  
  return errors;
}
```

### 7.2 Feedback Visual

Átomos con errores muestran:
- Halo rojo exterior
- Aparecen en la lista de errores inferior
- Badge contador de errores en header

---

## 8. Interactividad

### 8.1 Modos de Herramienta

| Modo | Cursor | Acción Click |
|------|--------|--------------|
| `select` | Pointer | Seleccionar átomo |
| `add-slm` | Crosshair | Añadir átomo SLM |
| `add-aod` | Crosshair | Añadir átomo AOD |

### 8.2 Controles del Usuario

- **Slider Blockade Radius**: 4-15 µm
- **Slider Min Distance**: 2-10 µm
- **Toggle Show Blockade**: Mostrar/ocultar radios
- **Toggle Show Grid**: Mostrar/ocultar cuadrícula

---

## 9. Performance

| Métrica | Valor | Nota |
|---------|-------|------|
| Max átomos | 256 | Límite de schema |
| Validación | O(n²) | Aceptable para N ≤ 256 |
| Re-render | ~5ms | Con 100 átomos |
| SVG elements | ~500 | Canvas + átomos + decoraciones |

---

## 10. Accesibilidad

- Contraste de colores AAA para roles
- Etiquetas numéricas en átomos
- Tooltips en botones de toolbar
- Keyboard navigation (planned)

---

## 11. Integración

```tsx
import { AtomRegisterEditor, RegisterConfig } from '@/components/neutral-atom';

function MyPage() {
  const [config, setConfig] = useState<RegisterConfig>();
  
  return (
    <AtomRegisterEditor
      initialConfig={config}
      onChange={setConfig}
    />
  );
}
```

---

## 12. Trabajo Futuro

- [ ] Drag & drop de átomos
- [ ] Undo/redo
- [ ] Importar/exportar JSON
- [ ] Toolbar de zonas (añadir/eliminar)
- [ ] Animación de shuttle preview
