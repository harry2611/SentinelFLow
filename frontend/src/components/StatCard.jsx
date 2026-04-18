import { titleCase } from "../utils/formatters";

export default function StatCard({ label, value, hint, accent = "teal" }) {
  return (
    <article className={`stat-card stat-card-${accent}`}>
      <p className="stat-label">{titleCase(label)}</p>
      <h2>{value}</h2>
      <p className="stat-hint">{hint}</p>
    </article>
  );
}

