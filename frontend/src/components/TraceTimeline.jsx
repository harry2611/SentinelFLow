import { formatDateTime } from "../utils/formatters";

export default function TraceTimeline({ logs = [] }) {
  return (
    <div className="timeline">
      {logs.map((log) => (
        <div className="timeline-item" key={log.id}>
          <div className="timeline-marker" />
          <div className="timeline-content">
            <div className="timeline-meta">
              <strong>{log.agent_name}</strong>
              <span>{log.stage}</span>
              <span>{formatDateTime(log.created_at)}</span>
            </div>
            <p>{log.message}</p>
            {Object.keys(log.payload || {}).length > 0 ? (
              <pre>{JSON.stringify(log.payload, null, 2)}</pre>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}

