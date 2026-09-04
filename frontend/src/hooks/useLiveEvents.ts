import { useState, useEffect, useRef, useCallback } from "react";
import type { EventResponse, PaginatedEventResponse } from "../types/api";

export type WsConnectionStatus = "connected" | "reconnecting" | "disconnected" | "error";

const API_BASE_URL = "http://127.0.0.1:8000";
const WS_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname || "127.0.0.1"}:8000/api/v1/ws/events`;
const MAX_EVENTS = 150;
const RECONNECT_BASE_DELAY = 1000;
const RECONNECT_MAX_DELAY = 10000;
const HEARTBEAT_INTERVAL = 15000;
const POLL_INTERVAL = 3000;

export function useLiveEvents() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [status, setStatus] = useState<WsConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  // Helper to merge events without duplicates
  const mergeEvents = useCallback((incoming: EventResponse[]) => {
    setEvents((prev) => {
      const map = new Map<string, EventResponse>();
      // Incoming first
      incoming.forEach((e) => {
        if (e && e.id) map.set(e.id, e);
      });
      // Previous existing
      prev.forEach((e) => {
        if (e && e.id && !map.has(e.id)) map.set(e.id, e);
      });
      const combined = Array.from(map.values());
      // Sort newest first
      combined.sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());
      return combined.slice(0, MAX_EVENTS);
    });
  }, []);

  // 1. Initial & periodic REST fetch
  const fetchRecentEvents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/events?limit=100`);
      if (res.ok) {
        const json: PaginatedEventResponse | EventResponse[] = await res.json();
        const items = Array.isArray(json) ? json : json.items ?? [];
        mergeEvents(items);
      }
    } catch {
      // Backend maybe restarting
    }
  }, [mergeEvents]);

  const clearTimers = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  // 2. WebSocket connection
  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    if (wsRef.current) {
      try { wsRef.current.close(); } catch { /* ignore */ }
    }

    setStatus(reconnectAttempts.current > 0 ? "reconnecting" : "disconnected");

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        reconnectAttempts.current = 0;
        setStatus("connected");

        heartbeatTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, HEARTBEAT_INTERVAL);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data: EventResponse = JSON.parse(event.data);
          if (data && data.id) {
            mergeEvents([data]);
          }
        } catch {
          // Ignore malformed
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        setStatus("error");
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setStatus("disconnected");

        const delay = Math.min(
          RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts.current),
          RECONNECT_MAX_DELAY
        );
        reconnectAttempts.current += 1;
        setStatus("reconnecting");

        reconnectTimer.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, delay);
      };
    } catch {
      setStatus("error");
    }
  }, [mergeEvents]);

  useEffect(() => {
    mountedRef.current = true;
    fetchRecentEvents();
    connect();

    // Polling fallback every 3s to guarantee zero missed events
    pollTimer.current = setInterval(() => {
      fetchRecentEvents();
    }, POLL_INTERVAL);

    return () => {
      mountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        try { wsRef.current.close(); } catch { /* ignore */ }
        wsRef.current = null;
      }
    };
  }, [fetchRecentEvents, connect, clearTimers]);

  return { events, status };
}
