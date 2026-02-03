import { useState } from "react";
import { Atom, Send, FileJson, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    AtomRegisterEditor,
    RegisterConfig,
    AnalogSequenceTimeline,
    SequenceConfig,
    AnalogPulse,
} from "@/components/neutral-atom";

// =============================================================================
// EXAMPLE DATA
// =============================================================================

const EXAMPLE_REGISTER: RegisterConfig = {
    layoutType: "arbitrary",
    minAtomDistance: 4.0,
    blockadeRadius: 8.0,
    atoms: [
        { id: 0, x: 0, y: 0, role: "SLM" },
        { id: 1, x: 6, y: 0, role: "SLM" },
        { id: 2, x: 12, y: 0, role: "SLM" },
        { id: 3, x: 3, y: 5.2, role: "SLM" },
        { id: 4, x: 9, y: 5.2, role: "SLM" },
        { id: 5, x: 15, y: 5.2, role: "AOD", aod_row: 0, aod_col: 0 },
    ],
};

const EXAMPLE_SEQUENCE: SequenceConfig = {
    totalDuration: 3000,
    pulses: [
        {
            startTime: 0,
            omega: { type: "blackman", duration: 500, area: Math.PI / 2 },
            detuning: { type: "constant", duration: 500, amplitude: -10 },
            phase: 0,
        },
        {
            startTime: 600,
            omega: { type: "blackman", duration: 1000, area: Math.PI },
            detuning: { type: "blackman", duration: 1000, area: 20 },
            phase: 0,
        },
        {
            startTime: 1700,
            omega: { type: "gaussian", duration: 800, area: Math.PI / 2 },
            phase: Math.PI / 4,
        },
    ],
};

// =============================================================================
// NEUTRAL ATOM STUDIO COMPONENT
// =============================================================================

export function NeutralAtomStudio() {
    const [register, setRegister] = useState<RegisterConfig>(EXAMPLE_REGISTER);
    const [sequence, setSequence] = useState<SequenceConfig>(EXAMPLE_SEQUENCE);
    const [currentTime, setCurrentTime] = useState(0);
    const [activeTab, setActiveTab] = useState("register");

    // Generate JSON job for backend
    const generateJob = () => {
        return {
            name: "Neutral Atom Job",
            version: "2.0",
            device: {
                backend_id: "pasqal_fresnel",
            },
            register: {
                layout_type: register.layoutType,
                min_atom_distance: register.minAtomDistance,
                blockade_radius: register.blockadeRadius,
                atoms: register.atoms.map(a => ({
                    id: a.id,
                    x: a.x,
                    y: a.y,
                    role: a.role,
                    ...(a.aod_row !== undefined ? { aod_row: a.aod_row } : {}),
                    ...(a.aod_col !== undefined ? { aod_col: a.aod_col } : {}),
                })),
            },
            operations: sequence.pulses.map((p, i) => ({
                op_type: "global_pulse",
                start_time: p.startTime,
                omega: p.omega,
                detuning: p.detuning,
                phase: p.phase,
            })).concat([{
                op_type: "measure" as const,
                start_time: sequence.totalDuration,
                atom_ids: register.atoms.map(a => a.id),
            }] as any),
            simulation: {
                backend: "qutip",
                shots: 1000,
            },
        };
    };

    const handleExportJson = () => {
        const job = generateJob();
        const blob = new Blob([JSON.stringify(job, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "neutral_atom_job.json";
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleSubmitJob = async () => {
        const job = generateJob();
        console.log("Submitting job:", job);
        // TODO: POST to backend API
        alert("Job submitted! Check console for JSON payload.");
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-quantum-purple/10 flex items-center justify-center">
                        <Atom className="w-6 h-6 text-quantum-purple" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold quantum-text">Neutral Atom Studio</h1>
                        <p className="text-muted-foreground">
                            Editor visual para procesadores de átomos neutros • Pasqal / QuEra
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleExportJson}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar JSON
                    </Button>
                    <Button size="sm" onClick={handleSubmitJob}>
                        <Send className="w-4 h-4 mr-2" />
                        Ejecutar Job
                    </Button>
                </div>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="register">
                        <Atom className="w-4 h-4 mr-2" />
                        Registro
                    </TabsTrigger>
                    <TabsTrigger value="sequence">
                        <FileJson className="w-4 h-4 mr-2" />
                        Secuencia
                    </TabsTrigger>
                    <TabsTrigger value="json">
                        <FileJson className="w-4 h-4 mr-2" />
                        JSON Preview
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="register" className="mt-4">
                    <AtomRegisterEditor
                        initialConfig={register}
                        onChange={setRegister}
                    />
                </TabsContent>

                <TabsContent value="sequence" className="mt-4">
                    <AnalogSequenceTimeline
                        sequence={sequence}
                        currentTime={currentTime}
                        onCurrentTimeChange={setCurrentTime}
                    />
                </TabsContent>

                <TabsContent value="json" className="mt-4">
                    <div className="quantum-card p-6">
                        <h3 className="font-semibold mb-4 flex items-center gap-2">
                            <FileJson className="w-5 h-5" />
                            Job JSON (neutral_atom_job.schema.json)
                        </h3>
                        <pre className="p-4 rounded-lg bg-muted/30 overflow-auto max-h-96 text-sm font-mono">
                            {JSON.stringify(generateJob(), null, 2)}
                        </pre>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}

export default NeutralAtomStudio;
