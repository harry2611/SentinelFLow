import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./layouts/AppShell";
import DashboardPage from "./pages/DashboardPage";
import DemoPage from "./pages/DemoPage";
import IntegrationsPage from "./pages/IntegrationsPage";
import ReviewQueuePage from "./pages/ReviewQueuePage";
import TaskDetailPage from "./pages/TaskDetailPage";
import TasksPage from "./pages/TasksPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
        <Route path="/review" element={<ReviewQueuePage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/demo" element={<DemoPage />} />
      </Route>
    </Routes>
  );
}

