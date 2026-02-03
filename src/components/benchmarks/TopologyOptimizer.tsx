import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Zap, ArrowRight, LayoutGrid, Thermometer } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface OptimizationResult {
    initial_transport_cost: number;
    optimized_transport_cost: number;
    heating_reduction_percent: number;
    qubits_mapped: number;
    method: string;
}

export function TopologyOptimizer() {
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleOptimize = async () => {
        setIsLoading(true);
        try {
            const response = await fetch("http://localhost:8000/api/topology/optimize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": "quantum-dev-key-2026"
                },
                body: JSON.stringify({
                    num_qubits: 50,
                    num_gates: 250,
                    width: 20,
                    height: 20
                })
            });

            if (response.ok) {
                const data = await response.json();
                setResult(data);
            }
        } catch (error) {
            console.error("Optimization failed:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const chartData = result ? [
        { name: 'Standard (Random)', cost: result.initial_transport_cost, color: '#94a3b8' },
        { name: 'TILT-lite (Spectral)', cost: result.optimized_transport_cost, color: '#10b981' }
    ] : [];

    return (
        <div className="grid gap-6 md:grid-cols-2">
            <Card className="quantum-card">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <LayoutGrid className="w-5 h-5 text-primary" />
                        <CardTitle>Optimizador Topológico (TILT-lite)</CardTitle>
                    </div>
                    <CardDescription>
                        Minimización de transporte atómico basada en grafos espectrales (Zou et al., 2024).
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="p-4 rounded-lg bg-muted/30 border border-border">
                            <h4 className="text-sm font-medium mb-2">Parámetros de Simulación</h4>
                            <ul className="text-sm text-muted-foreground space-y-1">
                                <li>• Qubits: 50 (Neutral Atom Array)</li>
                                <li>• Puertas: 250 (Interacciones aleatorias)</li>
                                <li>• Grid: 20x20 AOD Lattice</li>
                                <li>• Algoritmo: Spectral Layout + Greedy Snap</li>
                            </ul>
                        </div>

                        <Button
                            onClick={handleOptimize}
                            disabled={isLoading}
                            className="w-full bg-quantum-glow hover:bg-quantum-glow/80 text-white"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Optimizando Grafo...
                                </>
                            ) : (
                                <>
                                    <Zap className="w-4 h-4 mr-2" />
                                    Ejecutar Optimización TILT
                                </>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {result && (
                <Card className="quantum-card bg-gradient-to-br from-background to-primary/5 border-primary/20">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            Resultados de Optimización
                            <Badge variant="outline" className="text-success border-success/30">
                                Success
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="grid grid-cols-2 gap-4 text-center">
                            <div className="p-3 bg-background/50 rounded-lg border">
                                <p className="text-xs text-muted-foreground mb-1">Costo Transporte (u.a.)</p>
                                <div className="flex items-center justify-center gap-2 text-destructive font-mono font-bold">
                                    {result.initial_transport_cost}
                                    <ArrowRight className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-success">{result.optimized_transport_cost}</span>
                                </div>
                            </div>
                            <div className="p-3 bg-success/10 rounded-lg border border-success/20">
                                <p className="text-xs text-muted-foreground mb-1">Reducción Calentamiento</p>
                                <div className="flex items-center justify-center gap-2 text-success font-bold text-xl">
                                    <Thermometer className="w-5 h-5" />
                                    -{result.heating_reduction_percent}%
                                </div>
                            </div>
                        </div>

                        <div className="h-[200px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--muted))" />
                                    <XAxis type="number" hide />
                                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))', color: 'hsl(var(--popover-foreground))' }}
                                    />
                                    <Bar dataKey="cost" radius={[0, 4, 4, 0]} barSize={32}>
                                        {chartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <p className="text-xs text-center text-muted-foreground">
                            * Reducción directa de $\Delta n_{vib}$ (vibrational heating) al minimizar cruces AOD.
                        </p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
