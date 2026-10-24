import React, { useEffect, useState } from "react";
import Head from "next/head";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface Issue {
  id: string;
  title: string;
  status: string;
  assignee_type: string;
  priority: number;
  created_at: string;
}

interface Telemetry {
  active_runners: number;
  trajectories_recorded: number;
  issues_open: number;
  jobs_active: number;
  timestamp: string;
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ background: "#1a1a2e", padding: "1rem", border: "1px solid #333" }}>
      <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{label}</div>
      <div style={{ fontSize: "1.5rem" }}>{value}</div>
    </div>
  );
}

export default function Home() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [newAssignee, setNewAssignee] = useState("agent");
  const [status, setStatus] = useState("unknown");

  const fetchIssues = async () => {
    try {
      const r = await fetch(`${API_URL}/board/issues`);
      const data = await r.json();
      setIssues(data.issues || []);
    } catch (e) {
      console.error("Failed to fetch issues", e);
    }
  };

  const fetchTelemetry = async () => {
    try {
      const r = await fetch(`${API_URL}/telemetry/summary`);
      setTelemetry(await r.json());
      const health = await fetch(`${API_URL}/health`);
      const hData = await health.json();
      setStatus(hData.status);
    } catch {
      setStatus("offline");
    }
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;
    const connect = () => {
      ws = new WebSocket(`${WS_URL}/ws/telemetry`);
      ws.onmessage = (e) => {
        setEvents((prev) => [e.data, ...prev].slice(0, 50));
        fetchIssues();
        fetchTelemetry();
      };
      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
    };
    connect();
    fetchIssues();
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 10000);
    return () => {
      clearInterval(interval);
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  const createIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;
    await fetch(`${API_URL}/board/issues`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle, assignee_type: newAssignee, priority: 3 }),
    });
    setNewTitle("");
    fetchIssues();
  };

  const statusColor = status === "operational" ? "#22c55e" : status === "degraded" ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ fontFamily: "monospace", background: "#0a0a0f", color: "#e2e8f0", minHeight: "100vh", padding: "2rem" }}>
      <Head><title>OpenMinds — Control Center</title></Head>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", margin: 0 }}>
          <span style={{ color: statusColor }}>●</span> OpenMinds Control Center
        </h1>
        <span style={{ fontSize: "0.8rem", opacity: 0.6 }}>v1.0.0 — {status}</span>
      </div>
      {telemetry && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
          <StatCard label="Active Runners" value={telemetry.active_runners} />
          <StatCard label="Open Issues" value={telemetry.issues_open} />
          <StatCard label="Active Jobs" value={telemetry.jobs_active} />
          <StatCard label="Trajectories" value={telemetry.trajectories_recorded} />
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "2rem" }}>
        <div>
          <h2 style={{ fontSize: "1rem", marginBottom: "1rem", opacity: 0.8 }}>Board</h2>
          <form onSubmit={createIssue} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="New issue title..."
              style={{ flex: 1, background: "#1a1a2e", border: "1px solid #333", color: "#e2e8f0", padding: "0.5rem", fontFamily: "monospace" }}
            />
            <select
              value={newAssignee}
              onChange={(e) => setNewAssignee(e.target.value)}
              style={{ background: "#1a1a2e", border: "1px solid #333", color: "#e2e8f0", padding: "0.5rem" }}
            >
              <option value="agent">agent</option>
              <option value="human">human</option>
            </select>
            <button type="submit" style={{ background: "#3b82f6", color: "#fff", border: "none", padding: "0.5rem 1rem" }}>Create</button>
          </form>
          <div>
            {issues.map((issue) => (
              <div key={issue.id} style={{ background: "#1a1a2e", padding: "0.75rem", marginBottom: "0.5rem", border: "1px solid #333" }}>
                <div>{issue.title}</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{issue.status} · {issue.assignee_type} · p{issue.priority}</div>
              </div>
            ))}
            {issues.length === 0 && <div style={{ opacity: 0.5 }}>No issues yet.</div>}
          </div>
        </div>
        <div>
          <h2 style={{ fontSize: "1rem", marginBottom: "1rem", opacity: 0.8 }}>Live events</h2>
          <div style={{ background: "#1a1a2e", padding: "0.75rem", border: "1px solid #333", maxHeight: "400px", overflow: "auto", fontSize: "0.75rem" }}>
            {events.map((ev, i) => <div key={i}>{ev}</div>)}
            {events.length === 0 && <div style={{ opacity: 0.5 }}>Waiting for events…</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
