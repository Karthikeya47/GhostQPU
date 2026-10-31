import type { ReactNode } from "react";

/** Plain-language "what am I looking at" note under a chart or interactive piece. */
export function Explain({ children, title = "What am I looking at?" }: { children: ReactNode; title?: string }) {
  return (
    <details className="explain">
      <summary>{title}</summary>
      <div className="explain-body">{children}</div>
    </details>
  );
}

/** The numbers behind a chart, for anyone who wants to check them. */
export function NumbersTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <details className="explain">
      <summary>Show the numbers</summary>
      <div className="scrollx explain-body">
        <table className="data">
          <thead><tr>{head.map((h) => <th key={h}>{h}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </details>
  );
}
