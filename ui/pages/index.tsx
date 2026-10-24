import Head from "next/head";
import React, { useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS = process.env.NEXT_PUBLIC_WS_URL || API.replace(/^http/, "ws");
const COLUMNS = [
  { status: "open", label: "Backlog", hint: "Awaiting assignment" },
  { status: "in_progress", label: "In progress", hint: "Work underway" },
  { status: "in_review", label: "In review", hint: "Human verification" },
  { status: "blocked", label: "Blocked", hint: "Requires attention" },
  { status: "closed", label: "Completed", hint: "Reviewed and closed" },
] as const;
type View = "board" | "activity" | "fleet" | "evidence";
type Issue = { id: string; title: string; body?: string; status: string; assignee_type: string; priority: number; created_at: string; updated_at?: string };
type Metrics = { active_runners: number; trajectories_recorded: number; issues_open: number; jobs_active: number; timestamp: string };
type Runner = { id: string; runner_id: string; status: string; capacity: number; last_heartbeat?: string };
type FeedItem = { id: string; label: string; at: string };
type Health = { status: string; checks?: Record<string, boolean> };
const fmt = (date?: string) => date ? new Date(date).toLocaleString() : "Not reported";
const short = (id: string) => id.slice(0, 8);
async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(API + path, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(path + ": HTTP " + response.status);
  return response.json() as Promise<T>;
}

export default function Home() {
  const [view, setView] = useState<View>("board");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [runners, setRunners] = useState<Runner[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [socketState, setSocketState] = useState("connecting");
  const [query, setQuery] = useState("");
  const [title, setTitle] = useState("");
  const [assignee, setAssignee] = useState("agent");
  const [priority, setPriority] = useState(3);
  const [newOpen, setNewOpen] = useState(false);

  const refresh = useCallback(async () => {
    const responses = await Promise.allSettled([
      getJSON<{ issues: Issue[] }>("/board/issues"),
      getJSON<Metrics>("/telemetry/summary"),
      getJSON<{ runners: Runner[] }>("/runners"),
      getJSON<Health>("/health"),
    ]);
    const [board, telemetry, fleet, status] = responses;
    if (board.status === "fulfilled") setIssues(board.value.issues ?? []);
    if (telemetry.status === "fulfilled") setMetrics(telemetry.value);
    if (fleet.status === "fulfilled") setRunners(fleet.value.runners ?? []);
    if (status.status === "fulfilled") setHealth(status.value);
    const failed = responses.map((result, index) => result.status === "rejected" ? ["Issues", "Telemetry", "Runners", "Health"][index] : null).filter(Boolean);
    setError(failed.length ? "Unable to load: " + failed.join(", ") + ". Check API connectivity and permissions." : "");
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
    const poll = setInterval(() => void refresh(), 15000);
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let disposed = false;
    const connect = () => {
      if (disposed) return;
      try {
        socket = new WebSocket(WS + "/ws/telemetry");
        socket.onopen = () => setSocketState("connected");
        socket.onmessage = (message) => {
          if (message.data === "pong") return;
          let label = "Event received";
          try {
            const event = JSON.parse(message.data);
            label = [event.type, event.issue_id ?? event.job_id ?? event.run_id].filter(Boolean).join(" · ") || label;
          } catch { label = String(message.data).slice(0, 160); }
          setFeed(old => [{ id: Date.now().toString() + Math.random(), label, at: new Date().toISOString() }, ...old].slice(0, 60));
          void refresh();
        };
        socket.onclose = () => { setSocketState("disconnected"); if (!disposed) retry = setTimeout(connect, 3500); };
        socket.onerror = () => socket?.close();
      } catch { setSocketState("disconnected"); retry = setTimeout(connect, 3500); }
    };
    connect();
    return () => { disposed = true; clearInterval(poll); if (retry) clearTimeout(retry); socket?.close(); };
  }, [refresh]);

  const visible = useMemo(() => issues.filter(issue => [issue.title, issue.id, issue.body ?? ""].join(" ").toLowerCase().includes(query.trim().toLowerCase())), [issues, query]);

  const createIssue = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim() || saving) return;
    setSaving(true);
    setSaveError("");
    try {
      const response = await fetch(API + "/board/issues", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim(), assignee_type: assignee, priority }),
      });
      if (!response.ok) throw new Error("Issue creation failed (HTTP " + response.status + ")");
      setTitle("");
      setNewOpen(false);
      await refresh();
    } catch (reason) { setSaveError(reason instanceof Error ? reason.message : "Issue creation failed"); }
    finally { setSaving(false); }
  };

  const nav: { id: View; label: string; glyph: string }[] = [
    { id: "board", label: "Work board", glyph: "▦" },
    { id: "activity", label: "Event stream", glyph: "◷" },
    { id: "fleet", label: "Runner fleet", glyph: "⬡" },
    { id: "evidence", label: "Evidence", glyph: "◇" },
  ];
  return (
    <div className="om-root">
      <Head><title>OpenMinds | Human + Agent Workspace</title><meta name="description" content="OpenMinds live operator board, worker fleet and verification evidence." /></Head>
      <aside className="om-rail">
        <div className="om-brand"><span className="om-logo">✳</span><div><strong>OPENMINDS</strong><small>HUMAN + AGENT OS</small></div></div>
        <div className="om-rail-label">WORKSPACE</div>
        <nav aria-label="Workspace navigation">
          {nav.map(link => <button key={link.id} type="button" className={"om-nav " + (view === link.id ? "active" : "")} onClick={() => setView(link.id)} aria-current={view === link.id ? "page" : undefined}><span aria-hidden="true">{link.glyph}</span>{link.label}</button>)}
        </nav>
        <div className="om-rail-spacer" />
        <div className="om-policy"><span className="om-policy-icon">⛨</span><div><strong>Approval boundaries</strong><p>Privileged worker controls remain unavailable until account authorization is verified.</p></div></div>
        <div className="om-rail-footer">CodesbyFebin <span>·</span> OpenMinds</div>
      </aside>

      <div className="om-main">
        <header className="om-topbar">
          <div className="om-breadcrumb"><span>OPENMINDS</span><span className="om-chevron">/</span><strong>{nav.find(item => item.id === view)?.label}</strong></div>
          <div className="om-top-actions"><span className={"om-health " + (health?.status === "operational" ? "good" : "warn")}><i />API {health?.status ?? "unknown"}</span><span className={"om-health " + (socketState === "connected" ? "good" : "warn")}><i />Events {socketState}</span><button className="om-refresh" type="button" onClick={() => void refresh()}>↻ Refresh</button></div>
        </header>
        <main>
          {error && <div role="alert" className="om-error">{error}</div>}
          <div className="om-intro"><div><div className="om-eyebrow">OPERATOR WORKSPACE / LIVE DATA</div><h1>{view === "board" ? "Team command board" : view === "activity" ? "Activity & events" : view === "fleet" ? "Execution fleet" : "Evidence & verification"}</h1><p>{view === "board" ? "Coordinate human and agent work with PostgreSQL-backed issues." : view === "activity" ? "Events received from the control plane in this browser session." : view === "fleet" ? "Runner records reported by the control plane, not simulated device telemetry." : "Only recorded evidence counts. Unimplemented traces and approvals are labeled clearly."}</p></div>{view === "board" && <button type="button" className="om-primary" onClick={() => setNewOpen(true)}>＋ New task</button>}</div>
          <section className="om-stats" aria-label="Control plane metrics">
            {([{label:"Open issues",value:metrics?.issues_open,sub:"Database count"}, {label:"Active jobs",value:metrics?.jobs_active,sub:"Pending or running"}, {label:"Active runners",value:metrics?.active_runners,sub:"Registered as active"}, {label:"Recorded steps",value:metrics?.trajectories_recorded,sub:"Stored trajectories"}]).map((stat) => <article className="om-stat" key={stat.label}><div className="om-stat-label">{stat.label}<span>↗</span></div><div className="om-stat-number">{stat.value ?? "—"}</div><div className="om-stat-sub">{stat.sub}</div></article>)}
          </section>

          {view === "board" && <>
            <div className="om-section-toolbar"><div><h2>All work items <span>{issues.length}</span></h2><p>Workflow status comes from persisted issue records.</p></div><label className="om-search"><span aria-hidden="true">⌕</span><input aria-label="Search issues" placeholder="Search tasks..." value={query} onChange={event => setQuery(event.target.value)} /></label></div>
            <section className="om-board" aria-label="Kanban board">
              {COLUMNS.map(column => { const items = visible.filter(issue => issue.status === column.status); return <div className="om-column" key={column.status}><div className="om-column-heading"><div><i className={"om-col-dot " + column.status} /><strong>{column.label}</strong><span>{items.length}</span></div><small>{column.hint}</small></div><div className="om-cards">{items.map(issue => <article className="om-task" key={issue.id}><div className="om-task-meta"><span className="om-task-id">#{short(issue.id)}</span><span className={"om-priority p" + issue.priority}>P{issue.priority}</span></div><h3>{issue.title}</h3>{issue.body && <p className="om-task-body">{issue.body}</p>}<div className="om-task-bottom"><span className="om-assignee">{issue.assignee_type === "agent" ? "⬡" : "◉"} {issue.assignee_type}</span><time title={fmt(issue.created_at)} dateTime={issue.created_at}>{issue.created_at ? new Date(issue.created_at).toLocaleDateString() : "—"}</time></div></article>)}{items.length === 0 && <div className="om-empty-col">{loading ? "Loading issues…" : query ? "No matches" : "No tasks in this stage"}</div>}</div></div>; })}
            </section>
            <div className="om-readonly">Status changes require an authorized workflow endpoint. Drag-and-drop and approvals are intentionally disabled.</div>
          </>}

          {view === "activity" && <section className="om-panel"><div className="om-panel-header"><h2>Control plane event stream</h2><span className="om-tag">{socketState}</span></div><p className="om-muted">Events are observed from the WebSocket and are not a durable audit log. Only events since this page opened appear here.</p><div aria-live="polite" className="om-events">{feed.length ? feed.map(event => <div className="om-event" key={event.id}><span className="om-event-indicator" /><div><strong>{event.label}</strong><small>{fmt(event.at)}</small></div></div>) : <div className="om-placeholder">No events observed in this session.</div>}</div></section>}
          {view === "fleet" && <section className="om-panel"><div className="om-panel-header"><h2>Registered runners</h2><span className="om-tag">{runners.length} records</span></div><div className="om-runner-list">{runners.length ? runners.map(runner => <article className="om-runner" key={runner.id}><div><strong>⬡ {runner.runner_id}</strong><small>Last heartbeat: {fmt(runner.last_heartbeat)}</small></div><div><span className="om-tag">{runner.status}</span><span className="om-capacity">Capacity {runner.capacity}</span></div></article>) : <div className="om-placeholder">No runners registered. A runner count of zero is not an availability claim.</div>}</div></section>}
          {view === "evidence" && <div className="om-evidence-grid"><section className="om-panel"><div className="om-panel-header"><h2>Recorded evidence</h2><span className="om-tag">DB aggregate</span></div><div className="om-evidence-count">{metrics?.trajectories_recorded ?? "—"}</div><p className="om-muted">Trajectory steps recorded. Detailed trace retrieval is not connected to this console.</p></section><section className="om-panel"><div className="om-panel-header"><h2>Release qualification</h2><span className="om-tag blocked">Not certified</span></div><p className="om-muted">No proof of independent review, tenant isolation, or hostile-worker testing is exposed by these endpoints. Do not interpret a healthy API as production readiness.</p><button type="button" className="om-disabled" disabled>Approval controls unavailable</button></section></div>}
          <footer className="om-footer">Data source: {API} <span>·</span> Last telemetry: {fmt(metrics?.timestamp)} <span>·</span> No demo records are injected</footer>
        </main>
      </div>

      {newOpen && <div className="om-overlay" onMouseDown={event => { if (event.target === event.currentTarget) setNewOpen(false); }}><section className="om-dialog" role="dialog" aria-modal="true" aria-labelledby="om-dialog-title"><div className="om-dialog-head"><div><div className="om-eyebrow">NEW WORK ITEM</div><h2 id="om-dialog-title">Create a task</h2></div><button type="button" aria-label="Close dialog" onClick={() => setNewOpen(false)}>✕</button></div><form onSubmit={createIssue}><label>Task title<input autoFocus required maxLength={200} placeholder="Describe the work to be done" value={title} onChange={event => setTitle(event.target.value)} /></label><label>Assigned to<select value={assignee} onChange={event => setAssignee(event.target.value)}><option value="agent">Agent</option><option value="human">Human</option></select></label><label>Priority<select value={priority} onChange={event => setPriority(Number(event.target.value))}>{[1,2,3,4,5].map(value => <option value={value} key={value}>P{value}</option>)}</select></label><p className="om-muted">Creates a PostgreSQL issue in Backlog. It does not automatically execute code or provision a worker.</p>{saveError && <p role="alert" className="om-form-error">{saveError}</p>}<div className="om-form-actions"><button type="button" onClick={() => setNewOpen(false)}>Cancel</button><button type="submit" className="om-primary" disabled={saving || !title.trim()}>{saving ? "Creating…" : "Create task"}</button></div></form></section></div>}

      <style>{`
        :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b1010;color:#e9f1ee;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select{font:inherit}button{cursor:pointer}.om-root{display:flex;min-height:100vh;background:#0b1010}.om-rail{width:250px;flex-shrink:0;border-right:1px solid #243130;background:#101717;display:flex;flex-direction:column;padding:26px 16px;min-height:100vh}.om-brand{display:flex;gap:12px;align-items:center;padding:0 10px 46px}.om-brand strong{letter-spacing:.13em;font-size:13px;display:block}.om-brand small{display:block;color:#7a9490;letter-spacing:.13em;font-size:9px;margin-top:5px}.om-logo{color:#bcfa65;background:#1f382b;width:38px;height:38px;border:1px solid #3e6641;border-radius:10px;display:grid;place-items:center;font-size:25px}.om-rail-label{font-size:10px;letter-spacing:.17em;color:#607d75;margin:0 12px 14px;font-weight:700}.om-rail nav{display:grid;gap:5px}.om-nav{display:flex;align-items:center;gap:13px;text-align:left;background:transparent;border:1px solid transparent;border-radius:10px;color:#a0b3af;padding:12px 14px;font-size:13px}.om-nav span{font-size:19px;color:#78958b;min-width:22px}.om-nav:hover{background:#1a2926}.om-nav.active{background:#1b342a;color:#d6fcbb;border-color:#365642;font-weight:700}.om-nav.active span{color:#aef466}.om-rail-spacer{flex:1}.om-policy{border:1px solid #33433b;background:#17221d;padding:13px;border-radius:12px;display:flex;gap:10px}.om-policy-icon{font-size:20px;color:#e8c77d}.om-policy strong{font-size:11px}.om-policy p{color:#899e93;font-size:10px;line-height:1.6;margin:7px 0 0}.om-rail-footer{font-size:10px;color:#718880;padding:22px 8px 2px}.om-rail-footer span{color:#a9ed5f}.om-main{flex:1;min-width:0}.om-topbar{height:65px;padding:0 36px;border-bottom:1px solid #273330;display:flex;align-items:center;justify-content:space-between;gap:16px;background:#101716}.om-breadcrumb{font-size:11px;letter-spacing:.08em;display:flex;align-items:center;gap:13px;color:#718981}.om-breadcrumb strong{color:#d6e8df}.om-chevron{color:#416457}.om-top-actions{display:flex;align-items:center;gap:14px}.om-health{font-size:10px;color:#a4b4a9;display:inline-flex;align-items:center;gap:7px;text-transform:capitalize;white-space:nowrap}.om-health i{width:6px;height:6px;border-radius:50%;background:#ddac59}.om-health.good i{background:#a8ed5e;box-shadow:0 0 10px #82d54855}.om-refresh{border:1px solid #374941;border-radius:8px;padding:8px 13px;background:#19231f;color:#b6ccc0;font-size:11px}.om-main main{padding:35px 36px 24px;max-width:1850px;margin:auto}.om-error{background:#39211e;border:1px solid #9e5041;color:#ffb5a9;border-radius:9px;padding:12px 15px;margin-bottom:20px;font-size:12px}.om-intro{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:27px}.om-eyebrow{font-size:10px;letter-spacing:.19em;color:#aaf067;font-weight:700}.om-intro h1{font-size:30px;letter-spacing:-.045em;font-weight:680;margin:9px 0 6px}.om-intro p{margin:0;color:#83988e;font-size:12px}.om-primary{border:1px solid #bbf67a;background:#b9f56a;color:#142118;padding:11px 18px;border-radius:9px;font-size:12px;font-weight:800;white-space:nowrap}.om-primary:hover{background:#d0ff9a}.om-primary:disabled{opacity:.55;cursor:wait}.om-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:36px}.om-stat{background:#141e1b;border:1px solid #2a3932;border-radius:13px;padding:18px 20px}.om-stat-label{font-size:11px;color:#9caf9f;display:flex;align-items:center;justify-content:space-between}.om-stat-label span{color:#587d63}.om-stat-number{font-size:31px;font-weight:700;letter-spacing:-.04em;margin:13px 0 6px}.om-stat-sub{font-size:10px;color:#627e70}.om-section-toolbar{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:17px}.om-section-toolbar h2,.om-panel h2{font-size:15px;margin:0;font-weight:650}.om-section-toolbar h2 span{background:#24392b;color:#b4ed83;border-radius:7px;padding:2px 8px;font-size:11px;margin-left:7px}.om-section-toolbar p{margin:6px 0 0;font-size:11px;color:#738e81}.om-search{display:flex;align-items:center;gap:9px;border:1px solid #34463c;background:#151f1b;border-radius:8px;padding:0 13px;color:#84a38d}.om-search input{background:none;border:0;outline:none;color:#e1f1e3;height:36px;min-width:210px;font-size:12px}.om-board{display:grid;grid-template-columns:repeat(5,minmax(190px,1fr));gap:12px;overflow-x:auto;padding-bottom:10px}.om-column{background:#111b18;border:1px solid #293930;border-radius:12px;min-height:390px;padding:13px;min-width:190px}.om-column-heading{padding:5px 2px 15px;border-bottom:1px solid #26372d;margin-bottom:12px}.om-column-heading>div{display:flex;align-items:center;gap:7px}.om-column-heading strong{font-size:11px;white-space:nowrap}.om-column-heading span{font-size:10px;margin-left:auto;background:#25382c;color:#bcd6bb;padding:2px 6px;border-radius:6px}.om-column-heading small{display:block;font-size:10px;color:#728d7d;margin:7px 0 0 17px}.om-col-dot{width:8px;height:8px;border-radius:50%;background:#799287}.om-col-dot.in_progress{background:#a9f56d}.om-col-dot.in_review{background:#e9c979}.om-col-dot.blocked{background:#e68c74}.om-col-dot.closed{background:#80bea8}.om-cards{display:grid;align-content:start;gap:10px}.om-task{background:#1b2922;border:1px solid #34463a;border-radius:10px;padding:13px;box-shadow:0 3px 10px #0002}.om-task-meta{display:flex;align-items:center;justify-content:space-between;gap:8px}.om-task-id{color:#819b8d;font-size:10px;font-family:ui-monospace,monospace}.om-priority{font-size:9px;color:#b4dd9a;background:#263e2a;border:1px solid #365a3b;border-radius:5px;padding:3px 6px}.om-priority.p1,.om-priority.p2{color:#f2b5a4;background:#3b2825;border-color:#684239}.om-task h3{font-size:12px;line-height:1.5;font-weight:630;margin:13px 0 19px;overflow-wrap:anywhere}.om-task-body{font-size:10px;color:#9caf9f;max-height:72px;overflow:hidden;line-height:1.5}.om-task-bottom{display:flex;justify-content:space-between;align-items:center;gap:5px;border-top:1px solid #32463a;padding-top:10px;font-size:10px;color:#809987}.om-assignee{font-weight:650;color:#c3d8c1;text-transform:capitalize}.om-empty-col{font-size:11px;text-align:center;color:#627f6a;padding:46px 8px;border:1px dashed #34473b;border-radius:8px}.om-readonly{font-size:10px;color:#82968a;margin-top:10px}.om-panel{border:1px solid #2c3a32;border-radius:13px;background:#151f1b;padding:24px;margin-top:3px;min-height:190px}.om-panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.om-tag{font-size:10px;border:1px solid #3d5c42;background:#213529;color:#b8e7a0;border-radius:6px;padding:5px 9px;text-transform:capitalize}.om-tag.blocked{background:#3a2d23;border-color:#70543a;color:#f4c28c}.om-muted{font-size:12px;line-height:1.7;color:#93a79b}.om-events{margin-top:25px}.om-event{display:flex;align-items:flex-start;gap:13px;border-top:1px solid #2a3c31;padding:15px 0}.om-event-indicator{width:8px;height:8px;background:#a7ef67;border-radius:50%;margin-top:5px}.om-event strong{display:block;font-family:ui-monospace,monospace;font-size:12px;overflow-wrap:anywhere}.om-event small,.om-runner small{display:block;color:#738e80;font-size:10px;margin-top:7px}.om-placeholder{padding:45px 15px;text-align:center;color:#799185;font-size:12px}.om-runner{display:flex;align-items:center;justify-content:space-between;gap:20px;border-top:1px solid #2a3c31;padding:18px 0}.om-runner strong{font-size:13px}.om-runner>div:last-child{display:flex;gap:12px;align-items:center}.om-capacity{font-size:11px;color:#91a794}.om-evidence-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.om-evidence-count{font-size:54px;color:#baf477;font-weight:750;margin:14px 0}.om-disabled{border:1px solid #465347;background:#252d27;color:#8f9d8d;opacity:.6;border-radius:7px;padding:10px;font-size:11px;cursor:not-allowed}.om-footer{font-size:10px;color:#657b6d;border-top:1px solid #25362c;margin-top:40px;padding-top:19px;overflow-wrap:anywhere}.om-footer span{color:#b5ef7d;margin:0 7px}.om-overlay{position:fixed;inset:0;background:#010604d9;z-index:20;display:grid;place-items:center;padding:15px}.om-dialog{width:min(100%,490px);background:#15211b;border:1px solid #446248;border-radius:15px;padding:25px;box-shadow:0 25px 100px #0009}.om-dialog-head{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:22px}.om-dialog-head h2{font-size:24px;margin:7px 0 0}.om-dialog-head button{border:0;background:none;color:#a4b5a6;font-size:18px}.om-dialog form{display:grid;gap:17px}.om-dialog label{display:grid;gap:8px;color:#bccdbe;font-size:11px;font-weight:700}.om-dialog input,.om-dialog select{border:1px solid #45604b;border-radius:8px;background:#0d1712;color:#e0f3e1;padding:12px;outline-color:#bbf77c;width:100%}.om-form-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:8px}.om-form-actions button:not(.om-primary){background:none;border:1px solid #435749;color:#becdbd;border-radius:9px;padding:10px 16px}.om-form-error{color:#ffafa5;font-size:12px}.om-dialog p{margin:0}@media(max-width:1100px){.om-board{grid-template-columns:repeat(5,minmax(230px,1fr))}.om-main main{padding:28px 22px}.om-topbar{padding:0 22px}.om-stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:760px){.om-root{display:block}.om-rail{width:100%;min-height:auto;padding:12px;display:block;border-right:0;border-bottom:1px solid #314033}.om-brand{padding:0 6px 12px}.om-rail-label,.om-rail-spacer,.om-policy,.om-rail-footer{display:none}.om-rail nav{display:flex;overflow:auto;gap:5px}.om-nav{flex-shrink:0;padding:9px;font-size:11px}.om-topbar{height:auto;min-height:55px;padding:10px 15px;flex-wrap:wrap}.om-top-actions{flex-wrap:wrap;gap:9px}.om-main main{padding:24px 14px}.om-intro{align-items:flex-start}.om-intro h1{font-size:24px}.om-intro p{line-height:1.6}.om-stats{gap:9px;margin-bottom:25px}.om-stat{padding:14px}.om-stat-number{font-size:24px}.om-section-toolbar{align-items:flex-start;flex-direction:column}.om-search,.om-search input{width:100%}.om-evidence-grid{grid-template-columns:1fr}.om-board{grid-template-columns:repeat(5,minmax(235px,1fr))}}
      `}</style>
    </div>
  );
}
