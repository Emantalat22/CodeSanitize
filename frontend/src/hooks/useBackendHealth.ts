import { useState, useEffect, useCallback } from 'react';
import { HealthResponse } from '../types';
import { getHealthStatus } from '../services/api';

export type ConnectionStatus = 'checking' | 'connected' | 'disconnected';

export interface BackendHealthState {
  status: ConnectionStatus;
  data: HealthResponse | null;
  latencyMs: number | null;
  error: string | null;
  lastChecked: Date | null;
  checkHealth: () => Promise<void>;
}

export function useBackendHealth(pollIntervalMs: number = 10000): BackendHealthState {
  const [status, setStatus] = useState<ConnectionStatus>('checking');
  const [data, setData] = useState<HealthResponse | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const result = await getHealthStatus();
      setData(result.data);
      setLatencyMs(result.latencyMs);
      setStatus('connected');
      setError(null);
      setLastChecked(new Date());
    } catch (err) {
      setStatus('disconnected');
      setData(null);
      setLatencyMs(null);
      setError(err instanceof Error ? err.message : 'Unable to connect to backend service');
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    // Initial check
    checkHealth();

    // Periodic polling
    const interval = setInterval(checkHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [checkHealth, pollIntervalMs]);

  return {
    status,
    data,
    latencyMs,
    error,
    lastChecked,
    checkHealth,
  };
}
