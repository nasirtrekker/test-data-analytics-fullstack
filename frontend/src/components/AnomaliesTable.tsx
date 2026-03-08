import React from "react";
import type { VideoRow } from "../types";

export default function AnomaliesTable({ rows }: { rows: VideoRow[] }) {
  const top = [...rows].sort((a,b) => b.views - a.views).slice(0, 15);
  return (
    <div style={{ overflowX: "auto" }}>
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
      <thead>
        <tr style={{ background: "linear-gradient(90deg, #10b981 0%, #059669 100%)", color: "white" }}>
          <th style={{ textAlign: "left", padding: "12px 8px", fontWeight: 700 }}>ID</th>
          <th style={{ textAlign: "left", padding: "12px 8px", fontWeight: 700 }}>Title</th>
          <th style={{ textAlign: "right", padding: "12px 8px", fontWeight: 700 }}>Views</th>
          <th style={{ textAlign: "right", padding: "12px 8px", fontWeight: 700 }}>Engagement</th>
        </tr>
      </thead>
      <tbody>
        {top.map((r, i) => (
          <tr
            key={r.video_id}
            style={{
              background: i % 2 === 0 ? "rgba(16, 185, 129, 0.05)" : "white",
              transition: "background 0.2s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(16, 185, 129, 0.15)"}
            onMouseLeave={(e) => e.currentTarget.style.background = i % 2 === 0 ? "rgba(16, 185, 129, 0.05)" : "white"}
          >
            <td style={{ padding: "10px 8px", borderBottom: "1px solid #e5e7eb", fontFamily: "monospace", fontSize: 12 }}>{r.video_id}</td>
            <td style={{ padding: "10px 8px", borderBottom: "1px solid #e5e7eb" }}>{r.title}</td>
            <td style={{ padding: "10px 8px", borderBottom: "1px solid #e5e7eb", textAlign: "right", fontWeight: 600, color: "#059669" }}>{r.views.toLocaleString()}</td>
            <td style={{ padding: "10px 8px", borderBottom: "1px solid #e5e7eb", textAlign: "right", fontWeight: 600, color: "#10b981" }}>{r.engagement_rate.toFixed(4)}</td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}
