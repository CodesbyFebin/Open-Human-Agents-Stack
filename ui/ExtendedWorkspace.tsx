import React from 'react';
import { AgentDiffVisualizer } from './AgentDiffVisualizer';

export const ExtendedWorkspace: React.FC = () => (
  <section className="p-8 text-zinc-300 space-y-4" aria-label="Evidence workspace">
    <h2 className="text-lg font-bold">Evidence &amp; Assets</h2>
    <p className="text-zinc-500">
      No verified artifact feed is connected. Authenticated evidence retrieval
      and review are pending integration.
    </p>
  </section>
);
