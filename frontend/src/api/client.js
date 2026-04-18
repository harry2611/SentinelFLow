import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

export async function fetchDashboard() {
  const { data } = await api.get("/analytics/overview");
  return data;
}

export async function fetchTasks(params = {}) {
  const { data } = await api.get("/tasks", { params });
  return data;
}

export async function fetchTask(taskId) {
  const { data } = await api.get(`/tasks/${taskId}`);
  return data;
}

export async function fetchReviewQueue() {
  const { data } = await api.get("/review/queue");
  return data;
}

export async function approveTask(taskId, payload) {
  const { data } = await api.post(`/review/${taskId}/approve`, payload);
  return data;
}

export async function rejectTask(taskId, payload) {
  const { data } = await api.post(`/review/${taskId}/reject`, payload);
  return data;
}

export async function fetchIntegrations() {
  const { data } = await api.get("/integrations");
  return data;
}

export async function updateIntegration(id, payload) {
  const { data } = await api.put(`/integrations/${id}`, payload);
  return data;
}

export async function testIntegration(id) {
  const { data } = await api.post(`/integrations/${id}/test`);
  return data;
}

export async function createTask(payload) {
  const { data } = await api.post("/tasks", payload);
  return data;
}

export async function runDemo(payload) {
  const { data } = await api.post("/demo/run", payload);
  return data;
}

