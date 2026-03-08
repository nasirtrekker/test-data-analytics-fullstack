import React from "react";
import type { Metrics } from "../types";

const cardColors = [
  { bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", text: "#fff" },
  { bg: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", text: "#fff" },
  { bg: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", text: "#fff" },
  { bg: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", text: "#fff" },
  { bg: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", text: "#fff" },
  { bg: "linear-gradient(135deg, #30cfd0 0%, #330867 100%)", text: "#fff" }
];

function Card({ t, v, idx }: { t: string; v: string; idx: number }) {
  const colors = cardColors[idx % cardColors.length];
  return (
    <div style={{
      background: colors.bg,
      borderRadius: 12,
      padding: 16,
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
      transition: "transform 0.2s",
      cursor: "default"
    }}
    onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-4px)"}
    onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
    >
      <div style={{ fontSize: 11, color: colors.text, opacity: 0.9, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>{t}</div>
      <div style={{ fontSize: 28, fontWeight: 900, color: colors.text, marginTop: 4 }}>{v}</div>
    </div>
  );
}

export default function Overview({ metrics }: { metrics: Metrics }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 14, marginBottom: 20 }}>
      <Card t="Videos" v={metrics.rows.toLocaleString()} idx={0} />
      <Card t="Total Views" v={metrics.total_views.toLocaleString()} idx={1} />
      <Card t="Avg Engagement" v={metrics.avg_engagement_rate.toFixed(4)} idx={2} />
      <Card t="Avg Watch/View" v={metrics.avg_watch_time_per_view.toFixed(2)} idx={3} />
      <Card t="Clusters" v={metrics.cluster_count.toString()} idx={4} />
      <Card t="Anomalies" v={metrics.anomaly_count.toString()} idx={5} />
    </div>
  );
}
