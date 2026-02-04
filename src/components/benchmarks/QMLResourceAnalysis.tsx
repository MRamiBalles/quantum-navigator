import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Database, TrendingUp, AlertTriangle, Speaker, Zap, Activity } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, AreaChart, Area } from 'recharts';
import { apiUrl, getApiHeaders } from "@/lib/api-config";

export function QMLResourceAnalysis() {
    const [qramData, setQramData] = useState<any[]>([]);
    const [phononicData, setPhononicData] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchAllData = async () => {
            setIsLoading(true);
            try {
                const [qramRes, phononicRes] = await Promise.all([
                    fetch(apiUrl("/api/benchmarks/qram"), { headers: getApiHeaders() }),
                    fetch(apiUrl("/api/benchmarks/qram/phononic"), { headers: getApiHeaders() })
                ]);

                if (qramRes.ok) setQramData(await qramRes.json());
                if (phononicRes.ok) setPhononicData(await phononicRes.json());

            } catch (error) {
                console.error("Failed to fetch QML data", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAllData();
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
            {/* Header: Overview */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card className="quantum-card col-span-2 bg-gradient-to-r from-background to-primary/5">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Activity className="w-5 h-5 text-primary" />
                            <CardTitle>QML Memory Architecture Analysis (v6.2)</CardTitle>
                        </div>
                        <CardDescription>
                            Investigación de latencia acústica y escalabilidad para la carga de datos masivos (Miao et al., 2025).
                        </CardDescription>
                    </CardHeader>
                </Card>

                {/* Economic Cost Chart */}
                <Card className="quantum-card">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Database className="w-5 h-5 text-primary" />
                            <CardTitle>Costo QRAM vs Angle Encoding</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={qramData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                                    <XAxis dataKey="dataset_size" tick={{ fontSize: 10 }} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))' }} />
                                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                                    <Line type="monotone" dataKey="economic_cost_angle" name="Angle Encoding" stroke="#ef4444" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="economic_cost_qram" name="QRAM (Logical)" stroke="#10b981" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Phononic Latency Chart */}
                <Card className="quantum-card border-primary/20 bg-primary/5">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Speaker className="w-5 h-5 text-primary" />
                            <CardTitle>Latencia Acústica (SAW Phonons)</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={phononicData}>
                                    <defs>
                                        <linearGradient id="colorLat" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="dataset_size" tick={{ fontSize: 10 }} />
                                    <YAxis label={{ value: 'ns', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 10 }} />
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))' }} />
                                    <Area type="monotone" dataKey="latency_ns" name="Latencia Fonónica" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorLat)" />
                                    <Area type="monotone" dataKey="optical_latency_ref_ns" name="Ref. Óptica" stroke="#94a3b8" fill="transparent" strokeDasharray="5 5" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Fidelity Penalty */}
                <Card className="quantum-card">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Zap className="w-5 h-5 text-warning" />
                            <CardTitle>Penalización de Fidelidad ($Q^2$-Router)</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {phononicData.slice(-1).map((item, idx) => (
                                <div key={idx} className="text-center">
                                    <div className="text-3xl font-bold text-warning">
                                        -{item.fidelity_penalty_percent}%
                                    </div>
                                    <p className="text-sm text-muted-foreground">Fidelidad Final para N={item.dataset_size}</p>
                                    <div className="mt-4 p-3 bg-muted/50 rounded border text-xs text-left">
                                        Cada nodo del router acústico introduce una pérdida de coherencia (F=95.3%). A gran escala (depth={item.depth}), la señal se degrada significativamente.
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Insights */}
                <Card className="quantum-card bg-warning/5 border-warning/20">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-warning" />
                            Limitación de Escala
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm">
                            A pesar del acceso O(log N), la QRAM fonónica actual se ve limitada por el "Time-of-Flight" acústico (~3000 m/s). Para datasets de N {'>'} 10⁵, la latencia supera la barrera de los 200ns, afectando la eficiencia del algoritmo QML.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
