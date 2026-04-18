import { titleCase } from "../utils/formatters";

export default function MemoryList({ items = [] }) {
  return (
    <div className="memory-list">
      {items.map((item) => (
        <article className="memory-card" key={`${item.task_id}-${item.classification}`}>
          <p className="memory-label">{titleCase(item.classification)}</p>
          <h4>{item.decision_text}</h4>
          <div className="memory-chip-row">
            {item.retrieved_cases?.map((example, index) => (
              <span className="memory-chip" key={index}>
                {example.content}
              </span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

