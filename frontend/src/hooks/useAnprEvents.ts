import { useState, useEffect, useCallback, useMemo } from "react";
import type { EventResponse, PaginatedEventResponse } from "../types/api";
import { groupAnprEvents } from "../lib/anpr";

const API_URL = "http://127.0.0.1:8000/api/v1/events?event_type=anpr&limit=200";

export function useAnprEvents() {
  const [rawEvents, setRawEvents] = useState<EventResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(API_URL);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data: PaginatedEventResponse | EventResponse[] = await res.json();
      const items = Array.isArray(data) ? data : data.items ?? [];
      setRawEvents(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch ANPR events");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const groupedEvents = useMemo(() => {
    return groupAnprEvents(rawEvents);
  }, [rawEvents]);

  return {
    events: rawEvents,
    rawEvents,
    groupedEvents,
    isLoading,
    error,
    refresh: fetchEvents,
  };
}
