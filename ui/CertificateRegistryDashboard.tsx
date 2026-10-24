// ui/CertificateRegistryDashboard.tsx
// Fleet certificate authority control panel

import React, { useState } from 'react';

interface RunnerLeaseMetric {
  runnerUuid: string;
  commonName: string;
  allocatedIp: string;
  leaseExpiresAt: string;
  keyStrength: '2048-bit RSA' | '4096-bit RSA';
  cryptoStatus: 'VERIFIED' | 'ROTATION_WARNING' | 'EXPIRED';
}

export const CertificateRegistryDashboard: React.FC = () => {
  const [leases, setLeases] = useState<RunnerLeaseMetric[]>([
    {
      runnerUuid: "run-fleet-401-x",
      commonName: "runner-compute-node-alpha.openminds.internal",
      allocatedIp: "10.0.4.12",
      leaseExpiresAt: "2028-05-14T09:00:00Z",
      keyStrength: "2048-bit RSA",
      cryptoStatus: "VERIFIED"
    },
    {
      runnerUuid: "run-fleet-102-y",
      commonName: "runner-legacy-node-omega.openminds.internal",
      allocatedIp: "192.168.1.45",
      leaseExpiresAt: "2026-11-01T00:00:00Z",
      keyStrength: "2048-bit RSA",
      cryptoStatus: "ROTATION_WARNING"
    }
  ]);

  return (
    <div className="w-full h-full bg-zinc-950 border border-zinc-900 rounded-xl p-6 font-mono text-[11px] text-zinc-400 select-none shadow-2xl relative overflow-hidden">
      <div className="flex justify-between items-center mb-6 pb-4 border-b border-zinc-900">
        <div>
          <div className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest">// PKI LEASE MANAGEMENT REGISTRY</div>
          <h2 className="text-sm font-bold text-zinc-100 tracking-tight mt-1">FLEET CERTIFICATE AUTHORITY CONTROL PANEL</h2>
        </div>
        <div className="text-right">
          <span className="text-zinc-600 block text-[9px]">ROOT CA METRIC STATUS</span>
          <span className="text-emerald-400 font-bold uppercase text-[10px]">SECURED // 4096-BIT ANCHOR ACTIVE</span>
        </div>
      </div>
      <div className="overflow-x-auto border border-zinc-900 rounded bg-zinc-950/60">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-900/40 border-b border-zinc-900 text-zinc-500 font-bold">
              <th className="p-3 uppercase tracking-wider text-[10px]">RUNNER IDENTITY</th>
              <th className="p-3 uppercase tracking-wider text-[10px]">COMMON NAME (CN)</th>
              <th className="p-3 uppercase tracking-wider text-[10px]">IP OVERLAY</th>
              <th className="p-3 uppercase tracking-wider text-[10px]">LEASE TIMERS</th>
              <th className="p-3 uppercase tracking-wider text-[10px] text-right">ENCLAVE SEC</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {leases.map((lease) => (
              <tr key={lease.runnerUuid} className="hover:bg-zinc-900/20 transition-colors">
                <td className="p-3 font-bold text-zinc-300">{lease.runnerUuid}</td>
                <td className="p-3 text-zinc-400 max-w-[240px] truncate">{lease.commonName}</td>
                <td className="p-3 text-zinc-500 font-bold">{lease.allocatedIp}</td>
                <td className="p-3 text-zinc-400">{new Date(lease.leaseExpiresAt).toLocaleDateString()}</td>
                <td className="p-3 text-right">
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-wide uppercase border ${
                    lease.cryptoStatus === 'VERIFIED' ? 'bg-emerald-950/30 border-emerald-500 text-emerald-400' :
                    lease.cryptoStatus === 'ROTATION_WARNING' ? 'bg-amber-950/30 border-amber-500 text-amber-400 animate-pulse' :
                    'bg-rose-950/30 border-rose-500 text-rose-400'
                  }`}>{lease.cryptoStatus.replace('_', ' ')}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-6 pt-3 border-t border-zinc-900 text-[10px] text-zinc-600 leading-normal flex justify-between items-center">
        <span>[PKI_ORCHESTRATOR] Dynamic rotational leases verify connection paths using end-to-end mTLS handshakes.</span>
        <span className="text-zinc-500 font-bold">LEASE_EPOCH: UTC_ACTIVE</span>
      </div>
    </div>
  );
};
