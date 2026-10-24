// ui/AgentDiffVisualizer.tsx
// Visual unified-diff renderer for agent code changes in chat threads

import React from 'react';

interface AgentDiffProps {
  filePath: string;
  diffPayload: string;
  authorAgent: string;
}

export const AgentDiffVisualizer: React.FC<AgentDiffProps> = ({
  filePath,
  diffPayload,
  authorAgent,
}) => {
  const diffLines = diffPayload.split('\n');

  return (
    <div className="w-full bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden font-mono text-[11px] shadow-2xl relative my-3 select-text">
      <div className="bg-zinc-900/40 px-4 py-2.5 border-b border-zinc-900 flex justify-between items-center text-[10px]">
        <div className="flex items-center gap-2">
          <span className="text-zinc-600 font-bold">// FILE TARGET:</span>
          <span className="text-indigo-400 font-bold">{filePath}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-zinc-600">MODIFIED BY:</span>
          <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 font-bold">{authorAgent}</span>
        </div>
      </div>
      <div className="p-4 overflow-x-auto max-h-72 overflow-y-auto space-y-px bg-zinc-950/80 backdrop-blur leading-relaxed">
        {diffLines.map((line, idx) => {
          let lineClass = 'text-zinc-400';
          let bgClass = 'bg-transparent';
          if (line.startsWith('+') && !line.startsWith('+++')) {
            lineClass = 'text-emerald-400';
            bgClass = 'bg-emerald-950/20 border-l-2 border-emerald-500/70 pl-1';
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            lineClass = 'text-rose-400';
            bgClass = 'bg-rose-950/20 border-l-2 border-rose-500/70 pl-1';
          } else if (line.startsWith('@@')) {
            lineClass = 'text-cyan-500 font-bold bg-zinc-900/40 px-1 rounded inline-block my-0.5';
          }
          return (
            <div key={idx} className={`w-full whitespace-pre ${lineClass} ${bgClass}`}>
              {line}
            </div>
          );
        })}
      </div>
      <div className="bg-zinc-900/20 border-t border-zinc-900 px-4 py-3 flex justify-between items-center text-[10px] text-zinc-500 pointer-events-auto">
        <span>[REVIEW_GATE] Review changes thoroughly before accepting push requests into production pipelines.</span>
        <div className="flex gap-2">
          <button className="bg-zinc-900 hover:bg-rose-950/40 border border-zinc-800 hover:border-rose-500/30 text-rose-400 font-bold px-3 py-1 rounded transition-all">
            REJECT CHANGES
          </button>
          <button className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-3 py-1 rounded shadow-sm transition-all">
            APPROVE CHANGE
          </button>
        </div>
      </div>
    </div>
  );
};
