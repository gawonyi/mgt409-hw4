import { createContext, ReactNode, useContext, useState } from "react";
import type { PageResults } from "./types";

// Shared state between the chat widget (which receives search results from the agent)
// and the page (which renders them as product cards).
interface PageResultsState {
  results: PageResults | null;
  version: number; // bumps on every new search so the page can scroll to the grid
  show: (r: PageResults) => void;
  clear: () => void;
}

const Ctx = createContext<PageResultsState | null>(null);

export function PageResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null);
  const [version, setVersion] = useState(0);
  return (
    <Ctx.Provider
      value={{
        results,
        version,
        show: (r) => {
          setResults(r);
          setVersion((v) => v + 1);
        },
        clear: () => setResults(null),
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function usePageResults(): PageResultsState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePageResults must be used inside <PageResultsProvider>");
  return ctx;
}
