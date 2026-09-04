import React, { createContext, useContext, useState } from "react";
import type { WsConnectionStatus } from "../hooks/useLiveEvents";

interface WsStatusContextValue {
  status: WsConnectionStatus;
  setStatus: (s: WsConnectionStatus) => void;
}

const WsStatusContext = createContext<WsStatusContextValue>({
  status: "disconnected",
  setStatus: () => {},
});

export const WsStatusProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [status, setStatus] = useState<WsConnectionStatus>("disconnected");
  return (
    <WsStatusContext.Provider value={{ status, setStatus }}>
      {children}
    </WsStatusContext.Provider>
  );
};

export function useWsStatus() {
  return useContext(WsStatusContext);
}
