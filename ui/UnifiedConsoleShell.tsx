// ui/UnifiedConsoleShell.tsx
// Unified workspace shell bridging board, flows, diagnostics, and assets

import React, { useState } from 'react';
import { OmniConsole } from './OmniConsole';
import { ExtendedWorkspace } from './ExtendedWorkspace';
import { MulticaBoard } from './MulticaBoard';
import { CircuitDiagnosticConsole } from './CircuitDiagnosticConsole';

type ActiveViewModule = 'WORKSPACE_BOARD' | 'NODE_FLOWS' | 'DIAGNOSTICS' | 'EXTENDED_ASSETS';

export const UnifiedConsoleShell: React.FC = () => {
  const [currentModule, setCurrentModule] = useState<ActiveViewModule>('WORKSPACE_BOARD');

  return (
    <div className="w-full h-screen bg-zinc-950 text-zinc-100 flex flex-col font-mono text-xs overflow-hidden select-none">
      <header className="h-14 border-b border-zinc-900 bg-zinc-900/30 px-6 flex items-center justify-between backdrop-blur">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.8)] animate-pulse"></span>
            <h1 className="text-xs font-bold tracking-widest text-zinc-200 uppercase">OPENMINDS OS v2.0</h1>
          </div>
          <nav className="flex items-center gap-1 border-l border-zinc-900 pl-6 space-x-1">
            {(['WORKSPACE_BOARD', 'NODE_FLOWS', 'DIAGNOSTICS', 'EXTENDED_ASSETS'] as ActiveViewModule[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setCurrentModule(tab)}
                className={`px-3 py-1.5 rounded transition-all duration-150 font-bold tracking-tight uppercase border text-[10px] ${
                  currentModule === tab
                    ? 'bg-zinc-900 border-zinc-800 text-indigo-400 shadow-sm'
                    : 'bg-transparent border-transparent text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </nav>
        </div>
        <div className="hidden md:flex items-center gap-4 text-[10px] text-zinc-500 border border-zinc-900 bg-zinc-950/80 px-4 py-1 rounded">
          <span className="text-amber-400">Live cluster metrics not connected</span>
        </div>
      </header>
      <div className="flex-1 w-full bg-zinc-950 overflow-hidden relative">
        {currentModule === 'WORKSPACE_BOARD' && <MulticaBoard />}
        {currentModule === 'NODE_FLOWS' && <OmniConsole />}
        {currentModule === 'EXTENDED_ASSETS' && <ExtendedWorkspace />}
        {currentModule === 'DIAGNOSTICS' && (
          <div className="p-8 h-full overflow-y-auto space-y-6 max-w-5xl mx-auto">
            <CircuitDiagnosticConsole />
            <div className="bg-zinc-900/20 p-4 border border-zinc-900 rounded-xl space-y-2">
              <div className="text-[10px] text-indigo-400 font-bold">// DATA PLANE RELAY TOPOLOGY</div>
              <p className="text-zinc-500 leading-normal">Database replication telemetry is not connected. No live replication status is available.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
