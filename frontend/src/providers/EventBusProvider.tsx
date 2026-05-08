"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type EventType = 
  | "LEAD_HOT"
  | "CONVERSATION_HANDOFF"
  | "VOICE_LIVE_TRANSCRIPT"
  | "VOICE_INTERRUPTED"
  | "SYSTEM_ALERT"
  | "ORCHESTRATOR_STEP"
  | "BILLING_ALERT"
  | string;

export interface EventBusMessage {
  type: EventType;
  id?: string;
  event_id?: string;
  timestamp?: string;
  data?: any;
}

interface EventBusContextType {
  isConnected: boolean;
  subscribe: (eventTypes: EventType[], callback: (msg: EventBusMessage) => void) => () => void;
  history: EventBusMessage[];
}

const EventBusContext = createContext<EventBusContextType>({
  isConnected: false,
  subscribe: () => () => {},
  history: []
});

export function EventBusProvider({ children, tenantId }: { children: React.ReactNode, tenantId: string }) {
  const [isConnected, setIsConnected] = useState(false);
  const [history, setHistory] = useState<EventBusMessage[]>([]);
  // Use a ref to store listeners to avoid dependency cycles
  const listenersRef = React.useRef<{ types: Set<EventType>, cb: (msg: EventBusMessage) => void }[]>([]);
  
  const wsRef = React.useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    
    // Fallback to localhost if NEXT_PUBLIC_WS_URL is not set
    const wsUrlBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const wsUrl = `${wsUrlBase}/ws/v1/tenant/${tenantId}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      // Subscribe to all by default or let components handle it
      ws.send(JSON.stringify({ command: "subscribe", events: ["*"] }));
    };

    ws.onmessage = (event) => {
      try {
        const msg: EventBusMessage = JSON.parse(event.data);
        if (msg.type === "pong" || msg.type === "subscribed") return;
        
        // Add to global history
        setHistory(prev => {
          const newHistory = [msg, ...prev].slice(0, 100); // keep last 100
          return newHistory;
        });

        // Notify listeners
        listenersRef.current.forEach(({ types, cb }) => {
          if (types.has("*") || types.has(msg.type)) {
            cb(msg);
          }
        });
      } catch (err) {
        console.error("Error parsing WS message:", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect logic could be added here
    };

    return () => {
      ws.close();
    };
  }, [tenantId]);

  const subscribe = useCallback((eventTypes: EventType[], callback: (msg: EventBusMessage) => void) => {
    const listener = { types: new Set(eventTypes), cb: callback };
    listenersRef.current.push(listener);
    
    // Return unsubscribe function
    return () => {
      listenersRef.current = listenersRef.current.filter(l => l !== listener);
    };
  }, []);

  return (
    <EventBusContext.Provider value={{ isConnected, subscribe, history }}>
      {children}
    </EventBusContext.Provider>
  );
}

export const useEventBus = () => useContext(EventBusContext);
