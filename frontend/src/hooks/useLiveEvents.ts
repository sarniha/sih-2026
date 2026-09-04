import { useState, useEffect, useRef, useCallback } from "react";
import type { EventResponse } from "../types/api";

export type WsConnectionStatus = "connected" | "reconnecting" | "disconnected" | "error";

const WS_URL = "ws://localhost:8000/api/v1/ws/events";
const MAX_EVENTS = 100;
const RECONNECT_BASE_DELAY = 1000;
const RECONNECT_MAX_DELAY = 15000;
const HEARTBEAT_INTERVAL = 25000;

export function useLiveEvents() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [status, setStatus] = useState<WsConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  const clearTimers = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Close any lingering socket
    if (wsRef.current) {
      try { wsRef.current.close(); } catch { /* ignore */ }
    }

    setStatus(reconnectAttempts.current > 0 ? "reconnecting" : "disconnected");

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      reconnectAttempts.current = 0;
      setStatus("connected");

      // Heartbeat ping to keep connection alive
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
        setEvents((prev) => {
          const next = [data, ...prev];
          return next.length > MAX_EVENTS ? next.slice(0, MAX_EVENTS) : next;
        });
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus("error");
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      clearTimers();
      setStatus("disconnected");

      // Auto-reconnect with exponential backoff
      const delay = Math.min(
        RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts.current),
        RECONNECT_MAX_DELAY
      );
      reconnectAttempts.current += 1;
      setStatus("reconnecting");

      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current) {
          connect();
        }
      }, delay);
    };
  }, [clearTimers]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        try { wsRef.current.close(); } catch { /* ignore */ }
        wsRef.current = null;
      }
    };
  }, [connect, clearTimers]);

  return { events, status };
}
