// ui/WorkflowCanvas.tsx
// Visual workflow canvas with voice controls

import React, { useState, useEffect } from 'react';

interface NodeState {
  id: string;
  label: string;
  type: 'agent' | 'rag' | 'tool' | 'gate';
  status: 'idle' | 'running' | 'completed' | 'failed';
  latency?: number;
}

export const WorkflowCanvas: React.FC = () => {
  const [nodes, setNodes] = useState<NodeState[]>([
    { id: 'n1', label: 'Query Classification Router', type: 'agent', status: 'completed', latency: 320 },
    { id: 'n2', label: 'Workspace Context Vector Store', type: 'rag', status: 'running', latency: 150 },
    { id: 'n3', label: 'Isolated Shell Workspace Execution', type: 'tool', status: 'idle' }
  ]);
  
  const [isVoiceActive, setIsVoiceActive] = useState<boolean>(false);

  return (
    <div className="w-full h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/50 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold tracking-tight text-indigo-400">OpenMinds Console</span>
          <span className="px-2 py-0.5 text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded">Multi-Agent V2</span>
        </div>
        
        <button 
          onClick={() => setIsVoiceActive(!isVoiceActive)}
          className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 text-sm shadow-sm ${
            isVoiceActive 
              ? 'bg-emerald-500 text-white animate-pulse' 
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isVoiceActive ? 'bg-white' : 'bg-emerald-400'}`}></span>
          {isVoiceActive ? 'Voice Channel Connected' : 'Initiate Intercom Loop'}
        </button>
      </header>

      <main className="flex-1 p-8 grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-950 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px]">
        {nodes.map((node) => (
          <div 
            key={node.id} 
            className={`p-6 rounded-xl border transition-all duration-300 bg-slate-900/80 backdrop-blur relative overflow-hidden ${
              node.status === 'running' 
                ? 'border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.15)] ring-1 ring-indigo-500/30' 
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-xs uppercase tracking-widest font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {node.type}
              </span>
              <span className={`w-2 h-2 rounded-full ${
                node.status === 'completed' ? 'bg-emerald-400' :
                node.status === 'running' ? 'bg-indigo-400 animate-ping' : 'bg-slate-600'
              }`}></span>
            </div>

            <h3 className="font-semibold text-base text-slate-200 mb-1">{node.label}</h3>
            <p className="text-xs text-slate-500 font-mono">ID: {node.id}</p>

            {node.latency && (
              <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs font-mono text-slate-400">
                <span>Execution Duration:</span>
                <span className="text-indigo-400">{node.latency}ms</span>
              </div>
            )}
          </div>
        ))}
      </main>
    </div>
  );
};
