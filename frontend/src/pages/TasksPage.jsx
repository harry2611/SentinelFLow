import { useDeferredValue, useMemo, useState, startTransition } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchTasks } from "../api/client";
import Panel from "../components/Panel";
import TaskTable from "../components/TaskTable";

export default function TasksPage() {
  const [status, setStatus] = useState("");
  const [taskType, setTaskType] = useState("");
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const navigate = useNavigate();

  const queryParams = useMemo(
    () => ({
      status: status || undefined,
      task_type: taskType || undefined,
      search: deferredSearch || undefined,
    }),
    [status, taskType, deferredSearch],
  );

  const { data = [], isLoading } = useQuery({
    queryKey: ["tasks", queryParams],
    queryFn: () => fetchTasks(queryParams),
  });

  return (
    <div className="page-grid page-grid-workflows">
      <Panel
        title="Workflow Inventory"
        eyebrow="Search, inspect, and triage"
        className="panel-span-full workflow-panel"
      >
        <div className="filters">
          <input
            className="input"
            placeholder="Search title, requester, or description"
            value={search}
            onChange={(event) => {
              startTransition(() => {
                setSearch(event.target.value);
              });
            }}
          />
          <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="queued">Queued</option>
            <option value="in_progress">In progress</option>
            <option value="awaiting_review">Awaiting review</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="rejected">Rejected</option>
          </select>
          <select className="input" value={taskType} onChange={(event) => setTaskType(event.target.value)}>
            <option value="">All workflow types</option>
            <option value="support">Support</option>
            <option value="onboarding">Onboarding</option>
            <option value="internal_ops">Internal ops</option>
            <option value="follow_up">Follow up</option>
          </select>
        </div>
        {isLoading ? (
          <div className="empty-state">Loading workflow inventory...</div>
        ) : (
          <TaskTable tasks={data} onSelectTask={(task) => navigate(`/tasks/${task.id}`)} />
        )}
      </Panel>
    </div>
  );
}
