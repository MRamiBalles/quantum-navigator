import { useState, useEffect, useCallback, useRef } from "react";
import { WS_BASE_URL, API_BASE_URL, getApiKey } from "@/lib/api-config";

export interface PhysicsTelemetry {
  n_vib: number;
  velocity: number;
  fidelity: number;
  cumulative_atom_loss: number;
  decoder_backlog_ms: number;
  temperature_uk: number;
  refill_rate: number;
}

export interface TelemetryAlerts {
  heating_warning: boolean;
  backlog_warning: boolean;
  fidelity_critical: boolean;
}

export interface TelemetryMessage {
  type: "telemetry" | "complete" | "error";
  run_id: string;
  step?: number;
  progress?: number;
  physics?: PhysicsTelemetry;
  alerts?: TelemetryAlerts;
  timestamp?: number;
  status?: string;
  final_metrics?: {
    total_steps: number;
    duration_ms: number;
    cumulative_atom_loss: number;
    average_fidelity: number;
  };
  message?: string;
}

interface UseBenchmarkWebSocketOptions {
  serverUrl?: string;
  onTelemetry?: (data: TelemetryMessage) => void;
  onComplete?: (data: TelemetryMessage) => void;
  onError?: (error: string) => void;
}

export function useBenchmarkWebSocket(options: UseBenchmarkWebSocketOptions = {}) {
  const {
    serverUrl = WS_BASE_URL,
    onTelemetry,
    onComplete,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [telemetry, setTelemetry] = useState<PhysicsTelemetry | null>(null);
  const [alerts, setAlerts] = useState<TelemetryAlerts | null>(null);
  const [runId, setRunId] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(crypto.randomUUID());

  const connect = useCallback((benchmarkType: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const newRunId = crypto.randomUUID();
    setRunId(newRunId);

    const ws = new WebSocket(`${serverUrl}/ws/benchmarks/${clientIdRef.current}`);

    ws.onopen = () => {
      setIsConnected(true);
      setIsRunning(true);
      setProgress(0);
      
      // Send start command
      ws.send(JSON.stringify({
        command: "start",
        run_id: newRunId,
        benchmark_type: benchmarkType,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data: TelemetryMessage = JSON.parse(event.data);

        if (data.type === "telemetry") {
          setProgress(data.progress || 0);
          if (data.physics) setTelemetry(data.physics);
          if (data.alerts) setAlerts(data.alerts);
          onTelemetry?.(data);
        } else if (data.type === "complete") {
          setIsRunning(false);
          setProgress(100);
          onComplete?.(data);
        } else if (data.type === "error") {
          setIsRunning(false);
          onError?.(data.message || "Unknown error");
        }
      } catch (e) {
        console.error("Failed to parse telemetry:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      onError?.("WebSocket connection error");
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsRunning(false);
    };

    wsRef.current = ws;
  }, [serverUrl, onTelemetry, onComplete, onError]);

  const stop = useCallback(async () => {
    if (runId) {
      try {
        await fetch(`${API_BASE_URL}/api/benchmarks/stop/${runId}`, {
          method: "POST",
          headers: {
            "X-API-Key": getApiKey(),
          },
        });
      } catch (e) {
        console.error("Failed to stop benchmark:", e);
      }
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsRunning(false);
    setIsConnected(false);
  }, [runId]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsRunning(false);
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isRunning,
    progress,
    telemetry,
    alerts,
    runId,
    connect,
    stop,
    disconnect,
  };
}
