// ui/CircuitDiagnosticConsole.tsx
// Pydantic Graph circuit-breaker diagnostics panel

import React, { useState } from 'react';

interface ActiveGraphCircuit {
  workflowId: string;
  currentNode: 'PrimaryInferenceNode' | 'LocalFallbackNode' | 'TERMINATED';
  circuitTripped: boolean;
  activeEndpoint: string;
  accumulatedFailures: string[];
}

export const CircuitDiagnosticConsole: React.FC = () => {
  const [circuitState, setCircuitState] = useState<ActiveGraphCircuit>({
    workflowId: "wf-mesh-9841-alpha",
    currentNode: "LocalFallbackNode",
    circuitTripped: true,
    activeEndpoint: "http://localhost:8001/v1/orca [LOCAL_FLEET_NODE]",
    accumulatedFailures: [
      "401: Primary Cloud Inference degradation: API limit or cluster timeout reached.",
      "503: ConnectionError: Primary server failed verification handshake checks."
    ]
  });

  return (
    <div className="w-full bg-zinc-950 border border-zinc-900 rounded-xl font-mono text-[11px] p-6 text-zinc-400 select-none shadow-2xl relative overflow-hidden">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6 pb-4 border-b border-zinc-900">
        <div>
          <div className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">PYDANTIC GRAPH RUNTIME MONITOR</div>
          <h2 className="text-sm font-bold text-zinc-100 mt-1 tracking-tight">CONTEXT ID: {circuitState.workflowId}</h2>
        </div>
        <span className={`px-3 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${
          circuitState.circuitTripped
            ? 'bg-rose-950/40 border-rose-500 text-rose-400 animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.15)]'
            : 'bg-emerald-950/40 border-emerald-500 text-emerald-400'
        }`}>
          {circuitState.circuitTripped ? '🚨 CIRCUIT BROKEN // LOCAL FALLBACK ACTIVE' : 'OPTIMAL PRIMARY ROUTE'}
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4 border border-zinc-900 p-4 rounded bg-zinc-950/60">
          <div className="text-zinc-500 font-bold uppercase tracking-wider border-b border-zinc-900 pb-2">// LIVE NODE POSITION</div>
          <div className="space-y-2.5">
            <div className="flex justify-between items-center">
              <span className="text-zinc-600">CURRENT STATE TARGET:</span>
              <span className="text-zinc-200 font-bold bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">{circuitState.currentNode}</span>
            </div>
            <div className="flex justify-between items-baseline gap-4">
              <span className="text-zinc-600 whitespace-nowrap">ACTIVE METRIC HOST:</span>
              <span className="text-indigo-400 font-bold break-all text-right">{circuitState.activeEndpoint}</span>
            </div>
          </div>
        </div>
        <div className="space-y-3 border border-zinc-900 p-4 rounded bg-zinc-950/60 flex flex-col">
          <div className="text-zinc-500 font-bold uppercase tracking-wider border-b border-zinc-900 pb-2">
            // ACCUMULATED REGRESSION TIMELINE ({circuitState.accumulatedFailures.length})
          </div>
          <div className="flex-1 overflow-y-auto space-y-2 max-h-[110px] pr-1">
            {circuitState.accumulatedFailures.map((fail, index) => (
              <div key={index} className="p-2 border border-rose-950 bg-rose-950/10 text-rose-400 rounded leading-normal text-[10px]">{fail}</div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-6 pt-3 border-t border-zinc-900/80 text-[10px] text-zinc-600 leading-normal">
        [FAULT_TOLERANCE] Pydantic Graph engine systematically transparent. Automatic circuit routing fallback mechanisms intercept downstream processing degradation rules natively with zero pipeline interruptions.
      </div>
    </div>
  );
};
