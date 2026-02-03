import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ShieldAlert, ShieldCheck, Lock, Unlock } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';

export function CryptoResilience() {
    const [data, setData] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/benchmarks/crypto", {
                    headers: {
                        "X-API-Key": "quantum-dev-key-2026"
                    }
                });
                if (response.ok) {
                    const result = await response.json();
                    setData(result);
                }
            } catch (error) {
                console.error("Failed to fetch Crypto data", error);
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
                {/* Resource Cost Chart */}
                <Card className="quantum-card col-span-2">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Lock className="w-5 h-5 text-primary" />
                            <CardTitle>Recursos Shor (RSA/ECC) vs PQC</CardTitle>
                        </div>
                        <CardDescription>
                            Qubits lógicos estimados para romper criptografía actual (vulnerable) vs estándares NIST PQC (resistente).
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="hsl(var(--muted))" />
                                    <XAxis type="number" label={{ value: 'Qubits Lógicos Necesarios', position: 'insideBottom', offset: -5 }} />
                                    <YAxis type="category" dataKey="target" width={120} tick={{ fontSize: 12 }} />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', background: 'hsl(var(--popover))', color: 'hsl(var(--popover-foreground))' }}
                                    />
                                    <Bar dataKey="logical_qubits_needed" name="Qubits Lógicos" radius={[0, 4, 4, 0]} barSize={32}>
                                        {data.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.vulnerable ? '#ef4444' : '#10b981'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Status Indicators */}
                {data.map((item, index) => (
                    <Card key={index} className={`quantum-card border ${item.vulnerable ? 'border-destructive/30 bg-destructive/5' : 'border-success/30 bg-success/5'}`}>
                        <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-sm font-medium">{item.target}</CardTitle>
                                {item.vulnerable ? (
                                    <Unlock className="w-4 h-4 text-destructive" />
                                ) : (
                                    <ShieldCheck className="w-4 h-4 text-success" />
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">Estado:</span>
                                    <Badge variant={item.vulnerable ? "destructive" : "default"} className={!item.vulnerable ? "bg-success text-success-foreground hover:bg-success/80" : ""}>
                                        {item.vulnerable ? "VULNERABLE (Shor)" : "SECURE (PQC)"}
                                    </Badge>
                                </div>
                                {item.vulnerable && (
                                    <div className="flex justify-between text-xs mt-2">
                                        <span className="text-muted-foreground">Tiempo de Ruptura (Est.):</span>
                                        <span className="font-mono font-bold text-destructive">{item.estimated_break_time_hours} horas</span>
                                    </div>
                                )}
                                {!item.vulnerable && (
                                    <p className="text-xs text-muted-foreground mt-2">
                                        Resistente a ataques cuánticos conocidos (Lattice-based). Estandarizado en FIPS 203.
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
