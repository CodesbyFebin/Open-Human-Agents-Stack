// ui/MulticaBoard.tsx
// Human + agent collaborative board

import React, { useState } from 'react';

interface KanbanTask {
  id: string;
  title: string;
  assigneeName: string;
  assigneeType: 'human' | 'agent';
  status: 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE';
}

interface ChatBubble {
  id: string;
  sender: string;
  type: 'human' | 'agent';
  text: string;
}

export const MulticaBoard: React.FC = () => {
  const [tasks, setTasks] = useState<KanbanTask[]>([
    { id: 'task-1', title: 'Implement JWT Token Expiration Interceptors', assigneeName: 'Claude Code', assigneeType: 'agent', status: 'IN_PROGRESS' },
    { id: 'task-2', title: 'Refactor Multi-Region Database Connection Rings', assigneeName: 'Sarah Chen', assigneeType: 'human', status: 'REVIEW' },
    { id: 'task-3', title: 'Optimize RAG Context compactor functions', assigneeName: 'Aider Engine', assigneeType: 'agent', status: 'TODO' }
  ]);

  const [messages, setMessages] = useState<ChatBubble[]>([
    { id: 'm1', sender: 'Sarah Chen', type: 'human', text: '@Claude Code, please prioritize fixing task-1; the middleware requires updates.' },
    { id: 'm2', sender: 'Claude Code', type: 'agent', text: 'Acknowledged. Spawning execution sandbox container at workspace/task-1. Commencing file trace operations...' }
  ]);

  return (
    <div className="w-full h-screen bg-neutral-950 text-neutral-100 flex font-sans antialiased selection:bg-indigo-500/30">
      <section className="w-80 border-r border-neutral-900 bg-neutral-950 flex flex-col justify-between">
        <div className="p-4 border-b border-neutral-900 flex items-center justify-between">
          <span className="font-bold tracking-tight text-sm text-neutral-400"># squad-alpha-sync</span>
          <span className="px-2 py-0.5 text-[10px] bg-neutral-900 text-emerald-400 font-mono border border-neutral-800 rounded-full">Active Mesh</span>
        </div>
        
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="text-xs">
              <div className="flex items-baseline gap-2 mb-1">
                <span className={`font-bold ${msg.type === 'agent' ? 'text-indigo-400' : 'text-neutral-200'}`}>
                  {msg.sender}
                </span>
                <span className="text-[9px] text-neutral-600 font-mono uppercase tracking-wider">{msg.type}</span>
              </div>
              <p className="text-neutral-400 leading-relaxed bg-neutral-900/40 p-2.5 rounded border border-neutral-900/60 font-mono">
                {msg.text}
              </p>
            </div>
          ))}
        </div>
        
        <div className="p-4 border-t border-neutral-900 bg-neutral-950/80">
          <input 
            type="text" 
            placeholder="Instruct workspace or type message..." 
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-indigo-500 text-neutral-200 font-mono placeholder:text-neutral-600"
          />
        </div>
      </section>

      <main className="flex-1 flex flex-col overflow-hidden bg-neutral-900/20">
        <header className="h-14 border-b border-neutral-900 px-6 flex items-center justify-between bg-neutral-950/40 backdrop-blur">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold tracking-wide">MULTICA CENTRAL WORKSPACE BOARD</h2>
          </div>
        </header>

        <div className="flex-1 p-6 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-x-auto">
          {['TODO', 'IN_PROGRESS', 'REVIEW'].map((col) => (
            <div key={col} className="bg-neutral-950/60 rounded-xl border border-neutral-900 p-4 flex flex-col min-w-[280px]">
              <div className="flex items-center justify-between pb-3 border-b border-neutral-900 mb-4">
                <span className="text-xs font-bold uppercase tracking-widest text-neutral-400 font-mono">{col.replace('_', ' ')}</span>
                <span className="text-xs bg-neutral-900 px-2 py-0.5 rounded-full border border-neutral-800 text-neutral-500 font-mono">
                  {tasks.filter(t => t.status === col).length}
                </span>
              </div>

              <div className="flex-1 space-y-3 overflow-y-auto">
                {tasks.filter(t => t.status === col).map((task) => (
                  <div key={task.id} className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 hover:border-neutral-700 transition-all duration-200 group">
                    <h4 className="text-xs font-medium text-neutral-300 mb-4 leading-normal font-mono group-hover:text-neutral-100">{task.title}</h4>
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="text-neutral-500">Assignee:</span>
                      <span className={`px-2 py-0.5 rounded font-bold ${
                        task.assigneeType === 'agent' ? 'bg-indigo-950/50 text-indigo-400 border border-indigo-500/20' : 'bg-neutral-900 text-neutral-400 border border-neutral-800'
                      }`}>
                        {task.assigneeName}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};
