import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { fetchTask } from "../api/client";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import TraceTimeline from "../components/TraceTimeline";
import { formatDateTime, formatLatency, titleCase } from "../utils/formatters";

export default function TaskDetailPage() {
  const { taskId } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => fetchTask(taskId),
  });

  if (isLoading) {
    return <div className="empty-state">Loading full agent trace...</div>;
  }

  const latestDecision = data.decisions?.[0];
  const latestVerifier = data.verifier_results?.[0];

  return (
    <div className="page-grid">
      <Panel title={data.title} eyebrow={`${titleCase(data.task_type)} workflow`}>
        <div className="detail-header">
          <div className="chip-row">
            <StatusBadge value={data.status} />
            <span className="pill">{titleCase(data.execution_mode)}</span>
            <span className="pill">{titleCase(data.priority)}</span>
          </div>
          <p>{data.description}</p>
        </div>
        <div className="detail-grid">
          <div>
            <p className="detail-label">Requester</p>
            <strong>{data.requester_name}</strong>
            <p>{data.requester_email}</p>
          </div>
          <div>
            <p className="detail-label">Assignee</p>
            <strong>{data.assignee || "Pending"}</strong>
            <p>{data.department}</p>
          </div>
          <div>
            <p className="detail-label">Confidence</p>
            <strong>{data.confidence ? `${Math.round(data.confidence * 100)}%` : "Pending"}</strong>
            <p>Latency {formatLatency(data.latency_ms)}</p>
          </div>
          <div>
            <p className="detail-label">Workflow Created</p>
            <strong>{formatDateTime(data.created_at)}</strong>
            <p>{data.workflow.workflow_key}</p>
          </div>
        </div>
      </Panel>

      <Panel title="Decision Snapshot" eyebrow="Decision agent">
        {latestDecision ? (
          <div className="stack-list">
            <article className="list-card">
              <div className="list-card-top">
                <strong>{latestDecision.recommended_tool}</strong>
                <span>{Math.round(latestDecision.confidence * 100)}% confidence</span>
              </div>
              <p>{latestDecision.decision_text}</p>
              <small>{latestDecision.rationale}</small>
            </article>
            <pre>{JSON.stringify(latestDecision.action_plan, null, 2)}</pre>
          </div>
        ) : (
          <div className="empty-state">No decision recorded yet.</div>
        )}
      </Panel>

      <Panel title="Verifier Result" eyebrow="Quality gate">
        {latestVerifier ? (
          <div className="stack-list">
            <article className="list-card">
              <div className="list-card-top">
                <strong>{latestVerifier.passed ? "Passed" : "Flagged"}</strong>
                <StatusBadge value={latestVerifier.passed ? "completed" : "awaiting_review"} />
              </div>
              <p>{latestVerifier.summary}</p>
              <small>{latestVerifier.issues?.join(" • ") || "No issues reported"}</small>
            </article>
          </div>
        ) : (
          <div className="empty-state">Verifier has not run yet.</div>
        )}
      </Panel>

      <Panel title="Agent Trace" eyebrow="Shared state and execution timeline" className="panel-span-2">
        <TraceTimeline logs={data.execution_logs} />
      </Panel>

      <Panel title="Feedback Events" eyebrow="Learning signals">
        <div className="stack-list">
          {data.feedback_events.map((event) => (
            <article className="list-card" key={event.id}>
              <div className="list-card-top">
                <strong>{titleCase(event.event_type)}</strong>
                <span>{event.score !== null ? event.score : "n/a"}</span>
              </div>
              <p>{event.notes || "No note supplied"}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Agent State Snapshots" eyebrow="Persistent workflow state">
        <div className="stack-list">
          {data.agent_states.map((state) => (
            <article className="list-card" key={state.id}>
              <div className="list-card-top">
                <strong>{state.agent_name}</strong>
                <span>v{state.version}</span>
              </div>
              <pre>{JSON.stringify(state.state, null, 2)}</pre>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

