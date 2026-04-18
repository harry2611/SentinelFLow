import { titleCase } from "../utils/formatters";

export default function StatusBadge({ value }) {
  return <span className={`status-badge status-${value}`}>{titleCase(value)}</span>;
}

