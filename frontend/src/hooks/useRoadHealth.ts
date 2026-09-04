import { useState, useEffect, useCallback } from "react";
import type { RoadHealthSummaryResponse } from "../types/api";

const API_URL = "http://127.0.0.1:8000/api/v1/analytics/road-health";

export function useRoadHealth() {
  const [data, setData] = useState<RoadHealthSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRoadHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(API_URL);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const json: RoadHealthSummaryResponse = await res.json();
      setData(json);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch road health analytics"
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoadHealth();
  }, [fetchRoadHealth]);

  return {
    data,
    isLoading,
    error,
    refresh: fetchRoadHealth,
  };
}
