import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchIntegrations, testIntegration, updateIntegration } from "../api/client";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { formatDateTime, titleCase } from "../utils/formatters";

export default function IntegrationsPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["integrations"],
    queryFn: fetchIntegrations,
  });
  const [drafts, setDrafts] = useState({});

  useEffect(() => {
    const nextDrafts = {};
    data.forEach((integration) => {
      nextDrafts[integration.id] = {
        endpoint: integration.endpoint || "",
        is_enabled: integration.is_enabled,
      };
    });
    setDrafts(nextDrafts);
  }, [data]);

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }) => updateIntegration(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integrations"] }),
  });

  const testMutation = useMutation({
    mutationFn: (id) => testIntegration(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integrations"] }),
  });

  if (isLoading) {
    return <div className="empty-state">Loading integration inventory...</div>;
  }

  return (
    <div className="page-grid">
      <Panel title="Integrations" eyebrow="Webhook and system connectivity" className="panel-span-2">
        <div className="review-grid">
          {data.map((integration) => (
            <article className="review-card" key={integration.id}>
              <div className="review-card-top">
                <div>
                  <p className="panel-eyebrow">{titleCase(integration.integration_type)}</p>
                  <h3>{integration.name}</h3>
                </div>
                <StatusBadge value={integration.status} />
              </div>
              <div className="detail-grid">
                <div>
                  <p className="detail-label">Auth type</p>
                  <strong>{integration.auth_type || "n/a"}</strong>
                </div>
                <div>
                  <p className="detail-label">Last ping</p>
                  <strong>{formatDateTime(integration.last_ping_at)}</strong>
                </div>
              </div>
              <input
                className="input"
                placeholder="Webhook endpoint"
                value={drafts[integration.id]?.endpoint || ""}
                onChange={(event) =>
                  setDrafts((current) => ({
                    ...current,
                    [integration.id]: {
                      ...current[integration.id],
                      endpoint: event.target.value,
                    },
                  }))
                }
              />
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={Boolean(drafts[integration.id]?.is_enabled)}
                  onChange={(event) =>
                    setDrafts((current) => ({
                      ...current,
                      [integration.id]: {
                        ...current[integration.id],
                        is_enabled: event.target.checked,
                      },
                    }))
                  }
                />
                Enabled for agent execution
              </label>
              <div className="button-row">
                <button
                  className="button button-primary"
                  onClick={() =>
                    updateMutation.mutate({
                      id: integration.id,
                      payload: drafts[integration.id],
                    })
                  }
                >
                  Save
                </button>
                <button
                  className="button button-secondary"
                  onClick={() => testMutation.mutate(integration.id)}
                >
                  Test connection
                </button>
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

