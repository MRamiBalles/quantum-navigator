import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Database, TrendingUp, AlertTriangle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { apiUrl, getApiHeaders } from "@/lib/api-config";

export function QMLResourceAnalysis() {
    const [data, setData] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(apiUrl("/api/benchmarks/qram"), {
                    headers: getApiHeaders(),
                });
                if (response.ok) {
                    const result = await response.json();
                    setData(result);
                }
            } catch (error) {
                console.error("Failed to fetch QRAM data", error);
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
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                {/* Cost Analysis Chart */}
                <Card className="quantum-card col-span-2">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Database className="w-5 h-5 text-primary" />
                            <CardTitle>Costo Económico: QRAM vs Angle Encoding</CardTitle>
                        </div>
                        <CardDescription>
                            Comparativa de recursos físicos y lógicos para cargar datasets de diferentes tamaños (Wang et al., 2025).
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                                    <XAxis dataKey="dataset_size" label={{ value: 'Tamaño Dataset (N)', position: 'insideBottom', offset: -5 }} />
                                    <YAxis label={{ value: 'Coste (u.a.)', angle: -90, position: 'insideLeft' }} />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))', color: 'hsl(var(--popover-foreground))' }}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="economic_cost_angle" name="Angle Encoding (Sin QRAM)" stroke="#ef4444" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="economic_cost_qram" name="QRAM (Bucket Brigade)" stroke="#10b981" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                        <p className="text-xs text-center text-muted-foreground mt-4">
                            * El "Angle Encoding" crece linealmente en coste de hardware (O(N) qubits lógicos) o profundidad. La QRAM amortiza este coste con profundidad O(log N).
                        </p>
                    </CardContent>
                </Card>

                {/* Key Metrics */}
                <Card className="quantum-card">
                    <CardHeader>
                        <CardTitle className="text-sm">Barrera de Carga (Loss Barrier)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-4 text-warning">
                            <AlertTriangle className="w-8 h-8" />
                            <div>
                                <p className="text-sm text-muted-foreground">
                                    Para N {'>'} 1000, el Angle Encoding se vuelve inviable debido a la decoherencia acumulada en circuitos profundos.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Recommendation */}
                <Card className="quantum-card bg-success/5 border-success/20">
                    <CardHeader>
                        <CardTitle className="text-sm text-success">Recomendación Industrial</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm">
                            Para LLMs y datasets densos (N {'>'} 1024), es <strong>mandatorio</strong> el uso de QRAM fotónica o atómica para minimizar la profundidad del circuito de carga.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
