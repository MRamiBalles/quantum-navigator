import { useState, useMemo } from "react";
import { Play, Pause, SkipBack, SkipForward, Zap, Waves } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";

// =============================================================================
// TYPES
// =============================================================================

export type WaveformType = "constant" | "blackman" | "gaussian" | "interpolated";

export interface WaveformSpec {
    type: WaveformType;
    duration: number;  // nanoseconds
    amplitude?: number;
    area?: number;
    times?: number[];
    values?: number[];
}

export interface AnalogPulse {
    startTime: number;
    omega: WaveformSpec;
    detuning?: WaveformSpec;
    phase: number;
}

export interface SequenceConfig {
    pulses: AnalogPulse[];
    totalDuration: number;
}

// =============================================================================
// WAVEFORM GENERATORS
// =============================================================================

function generateBlackmanWaveform(duration: number, area: number, points: number = 100): number[] {
    const values: number[] = [];
    const peakAmplitude = area / (0.42 * duration);  // Approximate for Blackman

    for (let i = 0; i < points; i++) {
        const t = i / (points - 1);
        const blackman = 0.42 - 0.5 * Math.cos(2 * Math.PI * t) + 0.08 * Math.cos(4 * Math.PI * t);
        values.push(peakAmplitude * blackman);
    }

    return values;
}

function generateGaussianWaveform(duration: number, area: number, points: number = 100): number[] {
    const values: number[] = [];
    const sigma = duration / 6;  // 3-sigma on each side
    const center = duration / 2;
    const peakAmplitude = area / (sigma * Math.sqrt(2 * Math.PI));

    for (let i = 0; i < points; i++) {
        const t = (i / (points - 1)) * duration;
        const gaussian = Math.exp(-0.5 * ((t - center) / sigma) ** 2);
        values.push(peakAmplitude * gaussian);
    }

    return values;
}

function generateConstantWaveform(duration: number, amplitude: number, points: number = 100): number[] {
    return new Array(points).fill(amplitude);
}

function generateWaveform(spec: WaveformSpec, points: number = 100): number[] {
    switch (spec.type) {
        case "constant":
            return generateConstantWaveform(spec.duration, spec.amplitude ?? 0, points);
        case "blackman":
            return generateBlackmanWaveform(spec.duration, spec.area ?? Math.PI, points);
        case "gaussian":
            return generateGaussianWaveform(spec.duration, spec.area ?? Math.PI, points);
        case "interpolated":
            return spec.values ?? [];
        default:
            return [];
    }
}

// =============================================================================
// CONSTANTS
// =============================================================================

const TIMELINE_WIDTH = 700;
const TIMELINE_HEIGHT = 200;
const PADDING = { top: 30, right: 20, bottom: 40, left: 60 };
const PLOT_WIDTH = TIMELINE_WIDTH - PADDING.left - PADDING.right;
const PLOT_HEIGHT = (TIMELINE_HEIGHT - PADDING.top - PADDING.bottom) / 2 - 10;

// =============================================================================
// ANALOG SEQUENCE TIMELINE COMPONENT
// =============================================================================

interface AnalogSequenceTimelineProps {
    sequence: SequenceConfig;
    currentTime?: number;
    onCurrentTimeChange?: (time: number) => void;
    readOnly?: boolean;
}

export function AnalogSequenceTimeline({
    sequence,
    currentTime = 0,
    onCurrentTimeChange,
    readOnly = false,
}: AnalogSequenceTimelineProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState(1);

    // Calculate the full waveform data
    const waveformData = useMemo(() => {
        const totalDuration = sequence.totalDuration;
        const points = 200;
        const dt = totalDuration / points;

        const omega: number[] = new Array(points).fill(0);
        const detuning: number[] = new Array(points).fill(0);

        for (const pulse of sequence.pulses) {
            const startIdx = Math.floor(pulse.startTime / dt);
            const omegaWf = generateWaveform(pulse.omega, Math.ceil(pulse.omega.duration / dt));

            for (let i = 0; i < omegaWf.length && startIdx + i < points; i++) {
                omega[startIdx + i] += omegaWf[i];
            }

            if (pulse.detuning) {
                const detWf = generateWaveform(pulse.detuning, Math.ceil(pulse.detuning.duration / dt));
                for (let i = 0; i < detWf.length && startIdx + i < points; i++) {
                    detuning[startIdx + i] += detWf[i];
                }
            }
        }

        return { omega, detuning, totalDuration };
    }, [sequence]);

    // Generate SVG path from waveform
    const generatePath = (values: number[], maxValue: number, yOffset: number): string => {
        if (values.length === 0) return "";

        const scale = PLOT_HEIGHT / 2 / Math.max(maxValue, 1);
        const baseY = yOffset + PLOT_HEIGHT / 2;

        return values.map((v, i) => {
            const x = PADDING.left + (i / (values.length - 1)) * PLOT_WIDTH;
            const y = baseY - v * scale;
            return `${i === 0 ? "M" : "L"} ${x} ${y}`;
        }).join(" ");
    };

    // Calculate max values for scaling
    const maxOmega = Math.max(...waveformData.omega.map(Math.abs), 1);
    const maxDetuning = Math.max(...waveformData.detuning.map(Math.abs), 1);

    // Current time indicator position
    const timeIndicatorX = PADDING.left + (currentTime / waveformData.totalDuration) * PLOT_WIDTH;

    // Time axis labels
    const timeLabels = useMemo(() => {
        const labels = [];
        const duration = waveformData.totalDuration;
        const step = duration <= 1000 ? 200 : duration <= 5000 ? 1000 : 2000;

        for (let t = 0; t <= duration; t += step) {
            labels.push(t);
        }
        return labels;
    }, [waveformData.totalDuration]);

    const handleTimelineClick = (e: React.MouseEvent<SVGSVGElement>) => {
        if (readOnly) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left - PADDING.left;
        const t = (x / PLOT_WIDTH) * waveformData.totalDuration;

        onCurrentTimeChange?.(Math.max(0, Math.min(t, waveformData.totalDuration)));
    };

    return (
        <div className="quantum-card p-6 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Waves className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-semibold">Analog Pulse Sequence</h3>
                        <p className="text-sm text-muted-foreground">
                            Ω(t) y Δ(t) • Duración: {waveformData.totalDuration.toFixed(0)} ns
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Badge variant="outline" className="gap-1 font-mono">
                        <Zap className="w-3 h-3" />
                        {sequence.pulses.length} pulsos
                    </Badge>
                </div>
            </div>

            {/* Timeline SVG */}
            <svg
                width={TIMELINE_WIDTH}
                height={TIMELINE_HEIGHT}
                className="w-full h-auto cursor-crosshair"
                onClick={handleTimelineClick}
            >
                {/* Background */}
                <rect width="100%" height="100%" className="fill-card" rx={8} />

                {/* Grid lines */}
                {timeLabels.map(t => {
                    const x = PADDING.left + (t / waveformData.totalDuration) * PLOT_WIDTH;
                    return (
                        <line
                            key={`grid-${t}`}
                            x1={x}
                            y1={PADDING.top}
                            x2={x}
                            y2={TIMELINE_HEIGHT - PADDING.bottom}
                            className="stroke-muted/20"
                            strokeWidth={1}
                        />
                    );
                })}

                {/* Omega plot area */}
                <rect
                    x={PADDING.left}
                    y={PADDING.top}
                    width={PLOT_WIDTH}
                    height={PLOT_HEIGHT}
                    className="fill-primary/5"
                    rx={4}
                />

                {/* Detuning plot area */}
                <rect
                    x={PADDING.left}
                    y={PADDING.top + PLOT_HEIGHT + 10}
                    width={PLOT_WIDTH}
                    height={PLOT_HEIGHT}
                    className="fill-quantum-purple/5"
                    rx={4}
                />

                {/* Zero lines */}
                <line
                    x1={PADDING.left}
                    y1={PADDING.top + PLOT_HEIGHT / 2}
                    x2={PADDING.left + PLOT_WIDTH}
                    y2={PADDING.top + PLOT_HEIGHT / 2}
                    className="stroke-muted/40"
                    strokeDasharray="4 2"
                />
                <line
                    x1={PADDING.left}
                    y1={PADDING.top + PLOT_HEIGHT + 10 + PLOT_HEIGHT / 2}
                    x2={PADDING.left + PLOT_WIDTH}
                    y2={PADDING.top + PLOT_HEIGHT + 10 + PLOT_HEIGHT / 2}
                    className="stroke-muted/40"
                    strokeDasharray="4 2"
                />

                {/* Omega waveform */}
                <path
                    d={generatePath(waveformData.omega, maxOmega, PADDING.top)}
                    fill="none"
                    className="stroke-primary"
                    strokeWidth={2}
                />

                {/* Detuning waveform */}
                <path
                    d={generatePath(waveformData.detuning, maxDetuning, PADDING.top + PLOT_HEIGHT + 10)}
                    fill="none"
                    className="stroke-quantum-purple"
                    strokeWidth={2}
                />

                {/* Y-axis labels */}
                <text
                    x={PADDING.left - 8}
                    y={PADDING.top + PLOT_HEIGHT / 2}
                    textAnchor="end"
                    dominantBaseline="middle"
                    className="fill-primary text-xs font-medium"
                >
                    Ω
                </text>
                <text
                    x={PADDING.left - 8}
                    y={PADDING.top + PLOT_HEIGHT + 10 + PLOT_HEIGHT / 2}
                    textAnchor="end"
                    dominantBaseline="middle"
                    className="fill-quantum-purple text-xs font-medium"
                >
                    Δ
                </text>

                {/* Axis units */}
                <text
                    x={PADDING.left - 8}
                    y={PADDING.top + 10}
                    textAnchor="end"
                    className="fill-muted-foreground text-[10px]"
                >
                    rad/µs
                </text>

                {/* Time axis labels */}
                {timeLabels.map(t => {
                    const x = PADDING.left + (t / waveformData.totalDuration) * PLOT_WIDTH;
                    return (
                        <text
                            key={`label-${t}`}
                            x={x}
                            y={TIMELINE_HEIGHT - PADDING.bottom + 16}
                            textAnchor="middle"
                            className="fill-muted-foreground text-xs"
                        >
                            {t}
                        </text>
                    );
                })}

                <text
                    x={PADDING.left + PLOT_WIDTH / 2}
                    y={TIMELINE_HEIGHT - 8}
                    textAnchor="middle"
                    className="fill-muted-foreground text-xs"
                >
                    Tiempo (ns)
                </text>

                {/* Current time indicator */}
                <line
                    x1={timeIndicatorX}
                    y1={PADDING.top}
                    x2={timeIndicatorX}
                    y2={TIMELINE_HEIGHT - PADDING.bottom}
                    className="stroke-success"
                    strokeWidth={2}
                />
                <circle
                    cx={timeIndicatorX}
                    cy={PADDING.top - 5}
                    r={4}
                    className="fill-success"
                />

                {/* Current time label */}
                <text
                    x={timeIndicatorX}
                    y={PADDING.top - 12}
                    textAnchor="middle"
                    className="fill-success text-xs font-mono"
                >
                    {currentTime.toFixed(0)} ns
                </text>
            </svg>

            {/* Playback controls */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onCurrentTimeChange?.(0)}
                        disabled={readOnly}
                    >
                        <SkipBack className="w-4 h-4" />
                    </Button>
                    <Button
                        size="sm"
                        variant={isPlaying ? "default" : "outline"}
                        onClick={() => setIsPlaying(!isPlaying)}
                        disabled={readOnly}
                    >
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onCurrentTimeChange?.(waveformData.totalDuration)}
                        disabled={readOnly}
                    >
                        <SkipForward className="w-4 h-4" />
                    </Button>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Velocidad:</span>
                        <select
                            value={playbackSpeed}
                            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                            className="px-2 py-1 text-sm rounded border border-border bg-background"
                            disabled={readOnly}
                        >
                            <option value={0.25}>0.25x</option>
                            <option value={0.5}>0.5x</option>
                            <option value={1}>1x</option>
                            <option value={2}>2x</option>
                        </select>
                    </div>

                    <Slider
                        value={[currentTime]}
                        onValueChange={(v) => onCurrentTimeChange?.(v[0])}
                        min={0}
                        max={waveformData.totalDuration}
                        step={waveformData.totalDuration / 200}
                        className="w-40"
                        disabled={readOnly}
                    />
                </div>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-6 pt-2 border-t border-border text-sm">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 bg-primary" />
                    <span className="text-muted-foreground">Ω(t) - Frecuencia Rabi</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 bg-quantum-purple" />
                    <span className="text-muted-foreground">Δ(t) - Detuning</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-success" />
                    <span className="text-muted-foreground">Tiempo actual</span>
                </div>
            </div>
        </div>
    );
}

export default AnalogSequenceTimeline;
