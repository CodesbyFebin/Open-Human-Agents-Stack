// ui/MobileFrameBufferStream.tsx
// High-performance framebuffer polling canvas

import React, { useEffect, useRef, useState } from 'react';

interface FramebufferStreamProps {
  deviceId: string;
  platform: 'ANDROID' | 'IOS';
  refreshRateMs?: number;
}

export const MobileFrameBufferStream: React.FC<FramebufferStreamProps> = ({
  deviceId,
  platform,
  refreshRateMs = 100,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [streamActive, setStreamActive] = useState<boolean>(true);
  const [pipelineMetrics, setPipelineMetrics] = useState({ fps: 0, droppedFrames: 0, bandwidthKbps: 0 });

  useEffect(() => {
    if (!streamActive) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameCount = 0;
    let droppedCount = 0;
    let totalBytes = 0;
    let lastTime = performance.now();
    let trackingInterval: NodeJS.Timeout;

    const fetchLatestFrame = async () => {
      try {
        const startTime = performance.now();
        const frameUrl = `/api/mobile/frame-buffer?device_id=${encodeURIComponent(deviceId)}&platform=${platform}&ts=${startTime}`;
        const response = await fetch(frameUrl);
        if (!response.ok) throw new Error('Network ingestion dropped.');
        const blob = await response.blob();
        totalBytes += blob.size;
        const img = new Image();
        img.src = URL.createObjectURL(blob);
        img.onload = () => {
          if (canvas.width !== img.width || canvas.height !== img.height) {
            canvas.width = img.width;
            canvas.height = img.height;
          }
          ctx.drawImage(img, 0, 0);
          URL.revokeObjectURL(img.src);
          frameCount++;
        };
      } catch {
        droppedCount++;
      }
    };

    const loopRunner = setInterval(fetchLatestFrame, refreshRateMs);
    trackingInterval = setInterval(() => {
      const now = performance.now();
      const delta = (now - lastTime) / 1000;
      setPipelineMetrics({
        fps: Math.round(frameCount / delta),
        droppedFrames: droppedCount,
        bandwidthKbps: Math.round((totalBytes * 8) / 1024 / delta),
      });
      frameCount = 0;
      droppedCount = 0;
      totalBytes = 0;
      lastTime = now;
    }, 1000);

    return () => {
      clearInterval(loopRunner);
      clearInterval(trackingInterval);
    };
  }, [deviceId, platform, refreshRateMs, streamActive]);

  return (
    <div className="w-full bg-zinc-950 p-4 border border-zinc-900 rounded-xl font-mono text-[11px] text-zinc-400">
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-zinc-900">
        <span className="text-zinc-200 font-bold uppercase tracking-wider text-xs">// STREAMING FRAMEBUFFER: {deviceId}</span>
        <button
          onClick={() => setStreamActive(!streamActive)}
          className={`px-3 py-1 rounded text-[10px] font-bold border transition-all ${
            streamActive ? 'bg-indigo-950/40 border-indigo-500 text-indigo-400' : 'bg-zinc-900 border-zinc-800 text-zinc-600'
          }`}
        >
          {streamActive ? 'HALT INTERFACE POLLING' : 'RESUME POLLING'}
        </button>
      </div>
      <div className="flex flex-col lg:flex-row gap-4 items-center">
        <div className="relative border border-zinc-800 rounded bg-black overflow-hidden shadow-2xl">
          <canvas ref={canvasRef} className="max-w-full h-auto object-contain block max-h-[500px]" style={{ width: '280px' }} />
          {!streamActive && (
            <div className="absolute inset-0 bg-black/80 flex items-center justify-center text-zinc-600 text-xs uppercase tracking-widest animate-pulse">Stream Suspended</div>
          )}
        </div>
        <div className="flex-1 w-full space-y-2 border border-zinc-900 p-4 rounded bg-zinc-950/50">
          <div className="flex justify-between"><span className="text-zinc-600">INGESTION MATRIX RATE:</span><span className="text-zinc-200 font-bold">{pipelineMetrics.fps} FPS</span></div>
          <div className="flex justify-between"><span className="text-zinc-600">DATA BANDWIDTH THROUGHPUT:</span><span className="text-indigo-400 font-bold">{pipelineMetrics.bandwidthKbps} Kbps</span></div>
          <div className="flex justify-between"><span className="text-zinc-600">DROPPED TELEMETRY BLOCKS:</span><span className="text-rose-500 font-bold">{pipelineMetrics.droppedFrames}</span></div>
          <div className="pt-2 border-t border-zinc-900 text-[10px] text-zinc-500 leading-normal">
            [SYS] Frame buffer instances mapping directly to target hardware display layout boundaries.
          </div>
        </div>
      </div>
    </div>
  );
};
