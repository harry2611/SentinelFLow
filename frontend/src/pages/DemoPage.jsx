import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createTask, runDemo } from "../api/client";
import Panel from "../components/Panel";

const initialForm = {
  title: "",
  description: "",
  requester_name: "",
  requester_email: "",
  department: "Operations",
  task_type: "internal_ops",
  priority: "medium",
  execution_mode: "semi_autonomous",
};

export default function DemoPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState("");

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      setMessage("New workflow submitted and queued.");
      setForm(initialForm);
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    },
  });

  const demoMutation = useMutation({
    mutationFn: runDemo,
    onSuccess: () => {
      setMessage("Demo workflows created.");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    },
  });

  return (
    <div className="page-grid">
      <Panel title="Submit a Workflow" eyebrow="Interactive demo intake">
        <form
          className="form-grid"
          onSubmit={(event) => {
            event.preventDefault();
            createMutation.mutate({ ...form, auto_process: true, task_metadata: {} });
          }}
        >
          <input
            className="input"
            placeholder="Task title"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          />
          <input
            className="input"
            placeholder="Requester name"
            value={form.requester_name}
            onChange={(event) =>
              setForm((current) => ({ ...current, requester_name: event.target.value }))
            }
          />
          <input
            className="input"
            placeholder="Requester email"
            value={form.requester_email}
            onChange={(event) =>
              setForm((current) => ({ ...current, requester_email: event.target.value }))
            }
          />
          <input
            className="input"
            placeholder="Department"
            value={form.department}
            onChange={(event) =>
              setForm((current) => ({ ...current, department: event.target.value }))
            }
          />
          <select
            className="input"
            value={form.task_type}
            onChange={(event) => setForm((current) => ({ ...current, task_type: event.target.value }))}
          >
            <option value="support">Support triage</option>
            <option value="onboarding">Onboarding</option>
            <option value="internal_ops">Internal ops</option>
            <option value="follow_up">Follow-up automation</option>
          </select>
          <select
            className="input"
            value={form.execution_mode}
            onChange={(event) =>
              setForm((current) => ({ ...current, execution_mode: event.target.value }))
            }
          >
            <option value="manual">Manual approval</option>
            <option value="semi_autonomous">Semi-autonomous</option>
            <option value="autonomous">Fully autonomous</option>
          </select>
          <textarea
            className="textarea textarea-wide"
            placeholder="Describe the operational work that SentinelFlow should automate"
            value={form.description}
            onChange={(event) =>
              setForm((current) => ({ ...current, description: event.target.value }))
            }
          />
          <div className="button-row">
            <button className="button button-primary" type="submit">
              Submit workflow
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => demoMutation.mutate({ execution_mode: form.execution_mode })}
            >
              Generate full demo suite
            </button>
          </div>
          {message ? <p className="success-copy">{message}</p> : null}
        </form>
      </Panel>

      <Panel title="Demo Scenarios" eyebrow="Prebuilt business workflows">
        <div className="stack-list">
          {[
            "Support request triage with external webhook emission",
            "Employee onboarding checklist routing and access bundle creation",
            "Internal ops assignment with human review for high-risk spend",
            "Follow-up automation for unresolved customer requests",
          ].map((item) => (
            <article className="list-card" key={item}>
              <p>{item}</p>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

