// ui/XtermTerminalWrapper.tsx
// xterm.js terminal bound to Redis mesh hook

import React, { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { useRedisTerminal } from './hooks/useRedisTerminal';
import 'xterm/css/xterm.css';

interface XtermTerminalProps {
  sessionIdentity: string;
  podIdentity: string;
  authToken: string;
}

export const XtermTerminalWrapper: React.FC<XtermTerminalProps> = ({
  sessionIdentity,
  podIdentity,
  authToken,
}) => {
  const terminalElementRef = useRef<HTMLDivElement>(null);
  const xtermInstanceRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);

  const { connectionState, terminalBufferOutput, transmitTerminalInput } = useRedisTerminal({
    sessionIdentity,
    podIdentity,
    authToken,
  });

  useEffect(() => {
    if (!terminalElementRef.current) return;
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 12,
      fontFamily: 'Fira Code, Menlo, Monaco, Consolas, monospace',
      theme: {
        background: '#09090b',
        foreground: '#e4e4e7',
        cursor: '#6366f1',
        selectionBackground: 'rgba(99, 102, 241, 0.3)',
      },
      allowProposedApi: true,
    });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalElementRef.current);
    fitAddon.fit();
    xtermInstanceRef.current = term;
    fitAddonRef.current = fitAddon;

    term.onData((data) => transmitTerminalInput(data));

    const handleWindowResize = () => fitAddon.fit();
    window.addEventListener('resize', handleWindowResize);

    term.writeln('\x1b[1;34m[OPENMINDS // TERMINAL MESH INITIALIZED]\x1b[0m');
    term.writeln('Connecting tracking coordinates down to active runner PTY daemon...');

    return () => {
      window.removeEventListener('resize', handleWindowResize);
      term.dispose();
    };
  }, [sessionIdentity, podIdentity]);

  useEffect(() => {
    if (xtermInstanceRef.current && terminalBufferOutput) {
      xtermInstanceRef.current.write(terminalBufferOutput);
    }
  }, [terminalBufferOutput]);

  return (
    <div className="w-full h-full bg-zinc-950 border border-zinc-900 rounded-xl p-4 flex flex-col shadow-2xl relative">
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-zinc-900 text-[11px] font-mono">
        <div className="flex items-center gap-2">
          <span className="text-zinc-500 font-bold uppercase tracking-wider">RUNNER POD:</span>
          <span className="text-zinc-200 font-bold bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">{podIdentity}</span>
        </div>
        <span className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] border ${
          connectionState === 'STREAMING' ? 'bg-emerald-950/40 border-emerald-500 text-emerald-400' :
          connectionState === 'CONNECTING' ? 'bg-indigo-950/40 border-indigo-500 text-indigo-400 animate-pulse' :
          'bg-rose-950/40 border-rose-500 text-rose-400'
        }`}>{connectionState}</span>
      </div>
      <div className="flex-1 w-full overflow-hidden min-h-[300px]" ref={terminalElementRef} />
    </div>
  );
};
