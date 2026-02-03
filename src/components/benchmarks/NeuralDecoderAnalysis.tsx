import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, BrainCircuit, Network, Zap, Timer, ArrowRight, CheckCircle2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, LineChart, Line } from 'recharts';
import { apiUrl, getApiHeaders } from "@/lib/api-config";

export function NeuralDecoderAnalysis() {
    const [data, setData] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const response = await fetch(apiUrl("/api/benchmarks/decoder"), {
                    headers: getApiHeaders(),
                });
                if (response.ok) {
                    const result = await response.json();
                    setData(result);
                }
            } catch (error) {
                console.error("Failed to fetch decoder data", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    if (isLoading) {
        return (
            <div className="flex justify-center p-12">
                <Loader2 className="w-8 h-8 animate-spin text-quantum-glow" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card className="quantum-card col-span-2 bg-gradient-to-r from-background to-quantum-purple/10">
                    <CardHeader>
                        <div className="flex items-center gap-3">
                            <BrainCircuit className="w-6 h-6 text-quantum-purple" />
                            <CardTitle>Neural Decoder Analysis (v6.3)</CardTitle>
                            <Badge variant="outline" className="border-quantum-purple text-quantum-purple">GNN vs MWPM</Badge>
                        </div>
                        <CardDescription>
                            Comparativa de latencia en tiempo real para códigos qLDPC. El decodificador neuronal (GNN) ofrece inferencia O(1) paralela.
                        </CardDescription>
                    </CardHeader>
                </Card>

                {/* Main Latency Comparison Chart */}
                <Card className="quantum-card col-span-2 md:col-span-1">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Timer className="w-4 h-4 text-primary" />
                            Effective Cycle Time (ns)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                                    <XAxis dataKey="error_rate_p" label={{ value: 'Physical Error Rate (p)', position: 'insideBottom', offset: -5 }} />
                                    <YAxis label={{ value: 'Latency (ns)', angle: -90, position: 'insideLeft' }} />
                                    <Tooltip
                                        cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))' }}
                                    />
                                    <Legend />
                                    <Bar dataKey="gnn_latency_ns" name="GNN (Neural)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="mwpm_latency_ns" name="MWPM (Classical)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Advantage Ratio Chart */}
                <Card className="quantum-card col-span-2 md:col-span-1">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Zap className="w-4 h-4 text-warning" />
                            Accelerated Advantage
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                                    <XAxis dataKey="error_rate_p" />
                                    <YAxis label={{ value: 'Speedup Ratio (x)', angle: -90, position: 'insideLeft' }} />
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))' }} />
                                    <Line type="monotone" dataKey="advantage_ratio" name="GNN Speedup" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                        <p className="text-xs text-center text-muted-foreground mt-4">
                            * A medida que aumenta la tasa de error (p), MWPM se ralentiza exponencialmente. GNN se mantiene constante.
                        </p>
                    </CardContent>
                </Card>

                {/* Key Insights */}
                <div className="col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="quantum-card bg-success/5 border-success/20">
                        <CardHeader>
                            <CardTitle className="text-sm text-success flex items-center gap-2">
                                <CheckCircle2 className="w-4 h-4" />
                                Predictibilidad
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-xs">
                                GNN ofrece latencia determinista (~420ns), crucial para garantizar que el decodificador termine antes del siguiente ciclo de medición (1µs).
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="quantum-card">
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                <Network className="w-4 h-4" />
                                Arquitectura
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-xs text-muted-foreground">
                                Simulación de 8 capas de Message Passing en FPGA. Latencia de inferencia dominada por propagación de capas, no por complejidad del error.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="quantum-card">
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                <ArrowRight className="w-4 h-4" />
                                Next Steps
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-xs text-muted-foreground">
                                Validar inferencia en hardware real usando FPGA (Xilinx Alveo) para confirmar overhead de comunicación PCIe.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
