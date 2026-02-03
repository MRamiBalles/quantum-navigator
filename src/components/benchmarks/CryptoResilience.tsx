import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Loader2, ShieldAlert, ShieldCheck, Lock, Unlock, Calendar, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';
import { apiUrl, getApiHeaders } from "@/lib/api-config";

export function CryptoResilience() {
    const [data, setData] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [year, setYear] = useState<number>(2026);
    const [capacity, setCapacity] = useState<number>(0);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const response = await fetch(apiUrl(`/api/benchmarks/crypto?year=${year}`), {
                    headers: getApiHeaders(),
                });
                if (response.ok) {
                    const result = await response.json();
                    setData(result);
                    // Extract capacity from first result that has it
                    if (result.length > 0 && result[0].projected_capacity !== undefined) {
                        setCapacity(result[0].projected_capacity);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch Crypto data", error);
            } finally {
                setIsLoading(false);
            }
        };

        // Debounce slightly or just run
        const timer = setTimeout(() => fetchData(), 500);
        return () => clearTimeout(timer);
    }, [year]);

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                {/* Settings Panel */}
                <Card className="quantum-card col-span-2 bg-gradient-to-r from-background to-muted/20">
                    <CardHeader className="pb-2">
                        <div className="flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-primary" />
                            <CardTitle>Simulación Temporal: Roadmap de Hardware</CardTitle>
                        </div>
                        <CardDescription>Proyección de capacidad de Qubits Lógicos (IBM/QuEra/Google)</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <Label className="text-base font-semibold">Año Objetivo: {year}</Label>
                                <Badge variant="outline" className="text-primary border-primary/30">
                                    Capacidad Est: {capacity} Qubits Lógicos
                                </Badge>
                            </div>
                            <input
                                type="range"
                                min="2025"
                                max="2035"
                                step="1"
                                value={year}
                                onChange={(e) => setYear(parseInt(e.target.value))}
                                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-quantum-glow"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>2025 (NISQ)</span>
                                <span>2030 (Utility)</span>
                                <span>2035 (FTQC)</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Resource Cost Chart */}
                <Card className="quantum-card col-span-2">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Lock className="w-5 h-5 text-primary" />
                            <CardTitle>Recursos Shor vs Capacidad {year}</CardTitle>
                        </div>
                        <CardDescription>
                            Comparación de requisitos de qubits lógicos vs disponibilidad proyectada.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="hsl(var(--muted))" />
                                    <XAxis type="number" label={{ value: 'Qubits Lógicos', position: 'insideBottom', offset: -5 }} domain={[0, 'auto']} />
                                    <YAxis type="category" dataKey="target" width={140} tick={{ fontSize: 11 }} />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))', color: 'hsl(var(--popover-foreground))' }}
                                    />
                                    {/* Capacity Line Reference could be added here or visualized via color */}
                                    <Bar dataKey="logical_qubits_needed" name="Requeridos" radius={[0, 4, 4, 0]} barSize={20}>
                                        {data.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.vulnerable ? (entry.risk_status === 'BROKEN' ? '#ef4444' : entry.risk_status === 'CRITICAL' ? '#f59e0b' : '#3b82f6') : '#10b981'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Risk Cards */}
                {data.slice(0, 4).map((item, index) => (
                    <Card key={index} className={`quantum-card border ${item.risk_status === 'BROKEN' ? 'border-destructive/40 bg-destructive/5' : item.risk_status === 'CRITICAL' ? 'border-warning/40 bg-warning/5' : item.risk_status === 'SECURE' ? 'border-success/40 bg-success/5' : 'border-border bg-card'}`}>
                        <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-sm font-medium">{item.target}</CardTitle>
                                {item.risk_status === 'BROKEN' ? (
                                    <Unlock className="w-4 h-4 text-destructive animate-pulse" />
                                ) : item.risk_status === 'CRITICAL' ? (
                                    <AlertTriangle className="w-4 h-4 text-warning" />
                                ) : (
                                    <ShieldCheck className="w-4 h-4 text-success" />
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">Riesgo:</span>
                                    <Badge variant={item.risk_status === 'BROKEN' ? "destructive" : item.risk_status === 'CRITICAL' ? "secondary" : "default"}
                                        className={item.risk_status === 'SECURE' ? "bg-success text-success-foreground" : item.risk_status === 'CRITICAL' ? "bg-warning text-warning-foreground" : ""}>
                                        {item.risk_status || "UNKNOWN"}
                                    </Badge>
                                </div>
                                {item.risk_status === 'BROKEN' && (
                                    <p className="text-xs text-destructive font-semibold mt-2">
                                        ¡Peligro! Hardware capaz de romper cifrado en ~{item.estimated_break_time_hours} horas.
                                    </p>
                                )}
                                {item.risk_status === 'CRITICAL' && (
                                    <p className="text-xs text-warning font-semibold mt-2">
                                        Alerta: Capacidad {'>'} 10% de lo requerido. Migrar a PQC urgente.
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
