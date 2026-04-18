import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { approveTask, fetchReviewQueue, rejectTask } from "../api/client";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { titleCase } from "../utils/formatters";

export default function ReviewQueuePage() {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState({});

  const { data = [], isLoading } = useQuery({
    queryKey: ["review-queue"],
    queryFn: fetchReviewQueue,
  });

  const approveMutation = useMutation({
    mutationFn: ({ taskId, payload }) => approveTask(taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ taskId, payload }) => rejectTask(taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (isLoading) {
    return <div className="empty-state">Loading review queue...</div>;
  }

  return (
    <div className="page-grid">
      <Panel title="Human Review Queue" eyebrow="Approval gates for low-confidence or flagged runs" className="panel-span-2">
        <div className="review-grid">
          {data.map((task) => (
            <article className="review-card" key={task.id}>
              <div className="review-card-top">
                <div>
                  <p className="panel-eyebrow">{titleCase(task.task_type)}</p>
                  <h3>{task.title}</h3>
                </div>
                <StatusBadge value={task.status} />
              </div>
              <p>{task.description}</p>
              <div className="review-meta">
                <span>{task.requester_name}</span>
                <span>{titleCase(task.execution_mode)}</span>
                <span>{task.confidence ? `${Math.round(task.confidence * 100)}% confidence` : "Pending confidence"}</span>
              </div>
              <textarea
                className="textarea"
                placeholder="Add approval or rejection context"
                value={notes[task.id] || ""}
                onChange={(event) =>
                  setNotes((current) => ({ ...current, [task.id]: event.target.value }))
                }
              />
              <div className="button-row">
                <button
                  className="button button-primary"
                  onClick={() =>
                    approveMutation.mutate({
                      taskId: task.id,
                      payload: {
                        reviewer_name: "Operations Reviewer",
                        notes: notes[task.id],
                        override_complete: false,
                      },
                    })
                  }
                >
                  Approve / Resume
                </button>
                <button
                  className="button button-secondary"
                  onClick={() =>
                    approveMutation.mutate({
                      taskId: task.id,
                      payload: {
                        reviewer_name: "Operations Reviewer",
                        notes: notes[task.id],
                        override_complete: true,
                      },
                    })
                  }
                >
                  Override Complete
                </button>
                <button
                  className="button button-ghost"
                  onClick={() =>
                    rejectMutation.mutate({
                      taskId: task.id,
                      payload: {
                        reviewer_name: "Operations Reviewer",
                        notes: notes[task.id],
                      },
                    })
                  }
                >
                  Reject
                </button>
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

