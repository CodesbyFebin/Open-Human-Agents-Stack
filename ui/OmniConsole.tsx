// ui/OmniConsole.tsx
// Operator console with telemetry and voice intercom

import React, { useState, useEffect } from 'react';

interface TelemetryStream {
  nodeId: string;
  name: string;
  status: 'active' | 'stalled' | 'verified' | 'violating';
  promptTokens: number;
  completionTokens: number;
  accumulatedCost: number;
}

export const OmniConsole: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryStream[]>([
    { nodeId: 'node-mesh-101', name: 'Agent Autopilot Router', status: 'verified', promptTokens: 4210, completionTokens: 1840, accumulatedCost: 0.0321 },
    { nodeId: 'node-mesh-202', name: 'Workspace Coder Engine', status: 'active', promptTokens: 18240, completionTokens: 9410, accumulatedCost: 0.1842 },
    { nodeId: 'node-mesh-303', name: 'Production Guardrail Sentinel', status: 'violating', promptTokens: 1040, completionTokens: 210, accumulatedCost: 0.0041 }
  ]);

  const [voiceLoopActive, setVoiceLoopActive] = useState<boolean>(false);
  const [ledgerSyncStatus, setLedgerSyncStatus] = useState<string>('SYNCHRONIZED');

  return (
    <div className="w-full h-screen bg-slate-950 text-slate-50 flex flex-col font-mono text-xs overflow-hidden select-none">
      <header className="h-14 border-b border-slate-900 bg-slate-900/40 px-6 flex items-center justify-between backdrop-blur">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-bold tracking-wider text-indigo-400">OPENMINDS // OPERATOR CONSOLE</h1>
          <div className="flex items-center gap-2 border border-slate-800 bg-slate-950 px-2 py-0.5 rounded">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-400 uppercase">Ledger: {ledgerSyncStatus}</span>
          </div>
        </div>

        <button 
          onClick={() => setVoiceLoopActive(!voiceLoopActive)}
          className={`px-4 py-1.5 rounded border transition-all duration-150 flex items-center gap-2 font-semibold tracking-wide ${
            voiceLoopActive 
              ? 'bg-rose-950/40 border-rose-500 text-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.1)]' 
              : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-400'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${voiceLoopActive ? 'bg-rose-500 animate-ping' : 'bg-slate-600'}`}></span>
          {voiceLoopActive ? 'DISCONNECT AUDIO STREAM' : 'OPEN INTERCOM LOOP'}
        </button>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-px bg-slate-900 overflow-y-auto">
        {telemetry.map((stream) => (
          <div key={stream.nodeId} className="bg-slate-950 p-6 flex flex-col justify-between border-b border-slate-900/60 lg:border-none relative">
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{stream.nodeId}</span>
                <span className={`px-2 py-0.5 rounded uppercase font-bold text-[9px] border ${
                  stream.status === 'verified' ? 'bg-emerald-950/30 border-emerald-500 text-emerald-400' :
                  stream.status === 'active' ? 'bg-indigo-950/30 border-indigo-500 text-indigo-400' :
                  'bg-rose-950/30 border-rose-500 text-rose-400 animate-pulse'
                }`}>
                  {stream.status}
                </span>
              </div>

              <h2 className="text-sm font-semibold text-slate-200 tracking-tight mb-6">{stream.name}</h2>

              <div className="space-y-2 border-t border-slate-900/80 pt-4 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">PROMPT TOKENS:</span>
                  <span className="text-slate-300 font-bold">{stream.promptTokens.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">COMPLETION TOKENS:</span>
                  <span className="text-slate-300 font-bold">{stream.completionTokens.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-900 flex justify-between items-baseline">
              <span className="text-slate-500 text-[10px]">ACCUMULATED SPEND:</span>
              <span className="text-base font-bold text-indigo-400">${stream.accumulatedCost.toFixed(4)}</span>
            </div>
          </div>
        ))}
      </main>
    </div>
  );
};
