import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from "recharts";
import { fetchDashboard } from "../api/client";
import MemoryList from "../components/MemoryList";
import Panel from "../components/Panel";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { formatLatency, formatMinutes, titleCase } from "../utils/formatters";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
  });

  if (isLoading) {
    return <div className="empty-state">Loading dashboard analytics...</div>;
  }

  const metrics = data.headline_metrics;
  const statusBreakdown = Object.entries(data.status_counts).map(([status, count]) => ({
    status: titleCase(status),
    count,
  }));

  return (
    <div className="page-grid">
      <section className="stat-grid">
        <StatCard
          label="total workflows processed"
          value={metrics.total_workflows_processed}
          hint="Historical and seeded runs across all business scenarios"
        />
        <StatCard
          label="auto resolved workflows"
          value={metrics.auto_resolved_workflows}
          hint={`${metrics.manual_effort_reduced_pct}% of flows completed without human intervention`}
          accent="amber"
        />
        <StatCard
          label="time saved"
          value={formatMinutes(metrics.time_saved_minutes)}
          hint="Estimated manual effort avoided through routing and execution"
          accent="coral"
        />
        <StatCard
          label="average latency"
          value={formatLatency(metrics.average_latency_ms)}
          hint={`${metrics.review_queue_count} workflows currently waiting in review`}
          accent="blue"
        />
      </section>

      <Panel title="Resolution Trends" eyebrow="Ops throughput" className="panel-span-2">
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.resolution_trends}>
              <defs>
                <linearGradient id="completion" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00b894" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#00b894" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="completed"
                stroke="#00b894"
                fill="url(#completion)"
                strokeWidth={2}
              />
              <Area type="monotone" dataKey="failed" stroke="#ff7675" fillOpacity={0} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Status Mix" eyebrow="Current system load">
        <div className="chart-box compact-chart">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusBreakdown}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="status" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[10, 10, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Recent Decisions" eyebrow="Decision agent output">
        <div className="stack-list">
          {data.recent_decisions.slice(0, 5).map((decision) => (
            <article className="list-card" key={decision.task_id}>
              <div className="list-card-top">
                <strong>{titleCase(decision.classification)}</strong>
                <StatusBadge value={decision.confidence > 0.8 ? "completed" : "awaiting_review"} />
              </div>
              <p>{decision.summary}</p>
              <small>{Math.round(decision.confidence * 100)}% confidence via {decision.tool}</small>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Semantic Memory Retrieval" eyebrow="Compounding intelligence" className="panel-span-2">
        <MemoryList items={data.memory_retrieval_examples} />
      </Panel>

      <Panel title="Agent Trace Stream" eyebrow="Recent execution telemetry" className="panel-span-2">
        <div className="trace-stream">
          {data.recent_traces.slice(0, 8).map((trace, index) => (
            <article className="trace-row" key={`${trace.task_id}-${index}`}>
              <div>
                <p className="trace-stage">{trace.stage}</p>
                <strong>{trace.agent_name}</strong>
              </div>
              <p>{trace.message}</p>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

