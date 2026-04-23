import StatusBadge from "./StatusBadge";
import { formatLatency, formatRelativeDate, titleCase } from "../utils/formatters";

export default function TaskTable({ tasks, onSelectTask }) {
  return (
    <div className="table-wrap">
      <table className="task-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Type</th>
            <th>Status</th>
            <th>Mode</th>
            <th>Confidence</th>
            <th>Latency</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id} onClick={() => onSelectTask?.(task)}>
              <td className="task-table-main">
                <strong>{task.title}</strong>
                <p>{task.requester_name}</p>
              </td>
              <td>{titleCase(task.task_type)}</td>
              <td>
                <StatusBadge value={task.status} />
              </td>
              <td>{titleCase(task.execution_mode)}</td>
              <td>{task.confidence ? `${Math.round(task.confidence * 100)}%` : "Pending"}</td>
              <td>{formatLatency(task.latency_ms)}</td>
              <td>{formatRelativeDate(task.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
