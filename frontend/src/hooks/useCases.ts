import { useState, useEffect, useCallback } from "react";
import type { IncidentResponse, PaginatedIncidentResponse } from "../types/api";

const API_URL = "http://127.0.0.1:8000/api/v1/incidents";

export function useCases() {
  const [cases, setCases] = useState<IncidentResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}?limit=200`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data: PaginatedIncidentResponse | IncidentResponse[] = await res.json();
      const items = Array.isArray(data) ? data : data.items ?? [];
      // Sort newest first
      items.sort((a, b) => {
        const timeA = new Date(a.occurred_at || a.created_at).getTime();
        const timeB = new Date(b.occurred_at || b.created_at).getTime();
        return timeB - timeA;
      });
      setCases(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch incidents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const submitNewCase = useCallback(
    async (plate_text: string, notes?: string): Promise<boolean> => {
      const payload = {
        suspected_plate: plate_text.trim().toUpperCase(),
        notes: notes?.trim() || null,
        incident_type: "suspected_hit_and_run",
      };

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const errMsg = errJson?.detail || `HTTP ${res.status}: Failed to submit incident case`;
        throw new Error(errMsg);
      }

      await fetchCases();
      return true;
    },
    [fetchCases]
  );

  return {
    cases,
    isLoading,
    error,
    refresh: fetchCases,
    submitNewCase,
  };
}
