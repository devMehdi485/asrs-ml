import React, { createContext, useContext } from "react";
import { AsrsData, useAsrsData } from "./data";

const Ctx = createContext<{ data: AsrsData | null; error: string | null }>({
  data: null, error: null,
});

export function DataProvider({ children }: { children: React.ReactNode }) {
  const value = useAsrsData();
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useData = () => useContext(Ctx);
