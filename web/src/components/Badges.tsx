import { confidenceLevel, STATUS_LABELS } from "../format";
import type { DocStatus } from "../types";

export function StatusBadge({ status }: { status: DocStatus }) {
  return <span className={`badge status-${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}

/** Güven skorunu renk + metin olarak gösterir (renk körlüğü için yalnızca renge güvenmez). */
export function Confidence({ value }: { value: number | undefined }) {
  if (value === undefined) return null;
  const level = confidenceLevel(value);
  const text = { high: "yüksek", mid: "orta", low: "düşük", none: "" }[level];
  return (
    <span className={`conf conf-${level}`} title={`Güven: %${Math.round(value * 100)}`}>
      %{Math.round(value * 100)} {text}
    </span>
  );
}
