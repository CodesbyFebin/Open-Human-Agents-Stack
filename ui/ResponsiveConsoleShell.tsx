// ui/ResponsiveConsoleShell.tsx
// Adaptive shell for desktop and mobile touch views

import React, { useState } from 'react';
import { UnifiedConsoleShell } from './UnifiedConsoleShell';

export const ResponsiveConsoleShell: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [activeWorkspaceMode, setActiveWorkspaceMode] = useState<string>('PRODUCTION_SQUAD');

  return (
    <div className="w-full h-screen bg-zinc-950 flex flex-col md:flex-row overflow-hidden font-mono antialiased text-zinc-100 select-none">
      <header className="w-full h-14 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-4 md:hidden z-50">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
          <span className="font-bold text-xs tracking-wider text-zinc-200">OM OS MOBILE</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 border border-zinc-700 bg-zinc-800 rounded focus:outline-none focus:border-indigo-500 transition-colors"
        >
          <svg className="w-4 h-4 text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </header>

      <aside className={`w-full md:w-60 bg-zinc-950 border-r border-zinc-900 flex flex-col justify-between absolute md:relative inset-y-0 left-0 transform md:transform-none transition-transform duration-300 z-40 ${
        mobileMenuOpen ? 'translate-y-14 md:translate-y-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <div className="p-4 border-b border-zinc-900 bg-zinc-900/10 hidden md:block">
          <div className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">// SYSTEM DESK LAYOUT</div>
          <div className="text-zinc-200 text-xs font-bold mt-1 tracking-tight">OPENMINDS ORCHESTRATOR</div>
        </div>
        <div className="flex-1 p-4 space-y-4 overflow-y-auto">
          <div className="space-y-1.5">
            <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-wider block">ACTIVE RUNTIME TARGET</span>
            <select
              value={activeWorkspaceMode}
              onChange={(e) => setActiveWorkspaceMode(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded p-1.5 text-zinc-300 focus:outline-none focus:border-indigo-500 font-mono text-[10px]"
            >
              <option value="PRODUCTION_SQUAD">PROD_SQUAD_ALPHA (12 Nodes)</option>
              <option value="LOCAL_DAEMON">LOCAL_DAEMON_LOOP (1 Node)</option>
              <option value="ISOLATED_TEST">SANDBOX_TEST_ENV (4 Nodes)</option>
            </select>
          </div>
          <div className="pt-4 border-t border-zinc-900 space-y-2 text-[10px] text-zinc-500 leading-normal">
            <span className="text-indigo-400 font-bold block">// ADAPTIVE GRID OVERRIDES</span>
            <span>Mobile screen inputs automatically downscale absolute tracking coordinate inputs into native [0-1000] scale metrics.</span>
          </div>
        </div>
        <div className="p-4 border-t border-zinc-900 bg-zinc-900/10 font-mono text-[9px] text-zinc-600">
          <span>LEASE_STATUS: </span>
          <span className="text-emerald-400 font-bold">MUTATION_SYNCED</span>
        </div>
      </aside>

      <main className="flex-1 h-full w-full relative bg-zinc-950 overflow-hidden">
        <UnifiedConsoleShell />
      </main>
    </div>
  );
};
