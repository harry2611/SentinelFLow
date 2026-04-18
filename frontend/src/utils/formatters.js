import { formatDistanceToNow, format } from "date-fns";

export function titleCase(value = "") {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatRelativeDate(value) {
  if (!value) return "n/a";
  return formatDistanceToNow(new Date(value), { addSuffix: true });
}

export function formatDateTime(value) {
  if (!value) return "n/a";
  return format(new Date(value), "MMM d, yyyy h:mm a");
}

export function formatMinutes(minutes = 0) {
  if (minutes < 60) return `${minutes} min`;
  return `${(minutes / 60).toFixed(1)} hrs`;
}

export function formatLatency(ms = 0) {
  if (!ms) return "n/a";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

