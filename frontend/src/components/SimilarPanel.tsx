import React from "react";
import type { SimilarRow, VideoRow } from "../types";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function SimilarPanel(props: {
  rows: VideoRow[];
  selected: string;
  setSelected: (v: string) => void;
  similar: SimilarRow[];
}) {
  const top3 = props.similar.slice(0, 3);
  const scoreData = top3.map((s, i) => ({
    rank: `#${i + 1}`,
    score: Number(s.similarity.toFixed(3)),
    title: s.title,
  }));

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: "#f59e0b", fontWeight: 700, marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5 }}>🎯 Anchor video</div>
        <select
          value={props.selected}
          onChange={(e) => props.setSelected(e.target.value)}
          style={{
            width: "100%",
            padding: "10px",
            borderRadius: 8,
            border: "2px solid #fef3c7",
            fontSize: 13,
            background: "white",
            cursor: "pointer"
          }}
        >
          {props.rows.slice(0, 80).map(v => (
            <option key={v.video_id} value={v.video_id}>
              {v.video_id} — {v.title.slice(0, 52)}
            </option>
          ))}
        </select>
      </div>

      <div style={{ fontSize: 11, color: "#f59e0b", fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>📊 Similar titles (top 8)</div>

      <div style={{ height: 180, background: "#fffbeb", borderRadius: 8, padding: 8, marginBottom: 10, border: "1px solid #fde68a" }}>
        <div style={{ fontSize: 12, color: "#92400e", fontWeight: 700, marginBottom: 4 }}>
          Top-3 TF-IDF Cosine Similarity Scores
        </div>
        <ResponsiveContainer>
          <BarChart data={scoreData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="rank" />
            <YAxis domain={[0, 1]} />
            <Tooltip formatter={(value: number) => value.toFixed(3)} labelFormatter={(label) => `Rank ${label}`} />
            <Bar dataKey="score" fill="#f59e0b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ul style={{ paddingLeft: 0, listStyle: "none" }}>
        {props.similar.map(s => (
          <li
            key={s.video_id}
            style={{
              margin: "8px 0",
              padding: 10,
              borderRadius: 8,
              background: "linear-gradient(135deg, #fef3c7 0%, #fff 100%)",
              border: "1px solid #fde68a",
              transition: "transform 0.2s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = "translateX(4px)"}
            onMouseLeave={(e) => e.currentTarget.style.transform = "translateX(0)"}
          >
            <div style={{ fontWeight: 600, fontSize: 13, color: "#92400e", marginBottom: 4 }}>{s.title}</div>
            <div style={{ fontSize: 11, color: "#92400e", display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={{ background: "#fbbf24", color: "white", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                sim {s.similarity.toFixed(3)}
              </span>
              <span style={{ background: "#f59e0b", color: "white", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                {s.views.toLocaleString()} views
              </span>
              <span style={{ background: "#d97706", color: "white", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                {s.engagement_rate.toFixed(4)} eng
              </span>
            </div>
          </li>
        ))}
      </ul>

      <div style={{ fontSize: 12, color: "#78350f", marginTop: 8, lineHeight: 1.5 }}>
        Explanation: TF-IDF + cosine similarity is a standard baseline in information retrieval.
        Scores near 1.0 indicate stronger lexical overlap; top-3 are shown in the chart for quick comparison.
      </div>
    </div>
  );
}
