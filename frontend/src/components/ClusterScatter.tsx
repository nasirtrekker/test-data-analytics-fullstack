import React from "react";
import type { VideoRow } from "../types";
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, Legend, CartesianGrid, BarChart, Bar, Cell, LineChart, Line, ComposedChart } from "recharts";

const CLUSTER_COLORS = ["#8b5cf6", "#ec4899", "#06b6d4", "#10b981"];
const DBSCAN_COLORS = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626"];

type ClusteringDiagnostics = {
  kmeans: {
    silhouette: number | null;
    davies_bouldin: number | null;
    calinski_harabasz: number | null;
  };
  dbscan: {
    silhouette_non_noise: number | null;
    noise_count: number;
    noise_ratio: number;
    cluster_count_non_noise: number;
  };
};

export default function ClusterScatter({ rows, onSelect, diagnostics }: { rows: VideoRow[]; onSelect: (id: string) => void; diagnostics?: ClusteringDiagnostics }) {
  const rowsWithLogViews = rows.map((r) => ({
    ...r,
    views_log10: Math.log10(Math.max(1, r.views)),
  }));

  const clusters = Array.from(new Set(rows.map(r => r.cluster))).sort((a,b) => a-b);
  const series = clusters.map(c => ({
    name: `Cluster ${c}`,
    data: rowsWithLogViews.filter(r => r.cluster === c).map(r => ({
      video_id: r.video_id,
      x: r.views_log10,
      y: r.engagement_rate,
      title: r.title
    }))
  }));

  const dbscanLabels = Array.from(new Set(rowsWithLogViews.map((r) => r.dbscan_cluster))).sort((a, b) => a - b);
  const dbscanSeries = dbscanLabels.map((label) => ({
    name: label === -1 ? "DBSCAN Noise (-1)" : `DBSCAN ${label}`,
    data: rowsWithLogViews
      .filter((r) => r.dbscan_cluster === label)
      .map((r) => ({
        video_id: r.video_id,
        x: r.views_log10,
        y: r.engagement_rate,
        title: r.title,
      })),
    color: label === -1 ? "#dc2626" : DBSCAN_COLORS[Math.abs(label) % DBSCAN_COLORS.length],
  }));

  const kmeansDist = clusters.map((c, i) => ({
    label: `K${c}`,
    count: rowsWithLogViews.filter((r) => r.cluster === c).length,
    color: CLUSTER_COLORS[i % CLUSTER_COLORS.length],
  }));

  const dbscanDist = dbscanLabels.map((label) => ({
    label: label === -1 ? "noise" : `D${label}`,
    count: rowsWithLogViews.filter((r) => r.dbscan_cluster === label).length,
    color: label === -1 ? "#dc2626" : DBSCAN_COLORS[Math.abs(label) % DBSCAN_COLORS.length],
  }));

  const noiseCount = rowsWithLogViews.filter((r) => r.dbscan_cluster === -1).length;
  const noisePct = rowsWithLogViews.length > 0 ? (100 * noiseCount) / rowsWithLogViews.length : 0;

  // Calculate actual cluster statistics from current data
  const clusterStats = clusters.map(c => {
    const clusterRows = rows.filter(r => r.cluster === c);
    const avgViews = clusterRows.reduce((sum, r) => sum + r.views, 0) / clusterRows.length;
    const avgEng = clusterRows.reduce((sum, r) => sum + r.engagement_rate, 0) / clusterRows.length;
    const avgWatch = clusterRows.reduce((sum, r) => sum + (r.avg_watch_time_per_view || 0), 0) / clusterRows.length;
    return { cluster: c, count: clusterRows.length, avgViews, avgEng, avgWatch };
  });

  // Cluster labels and strategies
  const clusterInfo = {
    0: { name: "High Engagement", emoji: "🟣", color: "#8b5cf6", borderColor: "#8b5cf6", bgColor: "rgba(139, 92, 246, 0.1)", textColor: "#6d28d9", descColor: "#5b21b6", strategy: "Clone these success patterns" },
    1: { name: "Viral Reach", emoji: "🩷", color: "#ec4899", borderColor: "#ec4899", bgColor: "rgba(236, 72, 153, 0.1)", textColor: "#be185d", descColor: "#9f1239", strategy: "Great reach, improve retention" },
    2: { name: "Deep Engagement", emoji: "🩵", color: "#06b6d4", borderColor: "#06b6d4", bgColor: "rgba(6, 182, 212, 0.1)", textColor: "#0e7490", descColor: "#155e75", strategy: "Scale up this depth content" },
    3: { name: "Underperforming", emoji: "🟢", color: "#10b981", borderColor: "#10b981", bgColor: "rgba(16, 185, 129, 0.05)", textColor: "#047857", descColor: "#065f46", strategy: "Investigate root causes" },
  };

  return (
    <div style={{ width: "100%" }}>
      {diagnostics && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, marginBottom: 8 }}>
          <div style={{ background: "#eef2ff", borderRadius: 6, padding: 6 }}>
            <div style={{ fontSize: 10, color: "#4338ca", fontWeight: 700 }}>Silhouette</div>
            <div style={{ fontSize: 16, fontWeight: 900, color: "#3730a3" }}>
              {diagnostics.kmeans.silhouette != null ? diagnostics.kmeans.silhouette.toFixed(3) : "N/A"}
            </div>
          </div>
          <div style={{ background: "#fff7ed", borderRadius: 6, padding: 6 }}>
            <div style={{ fontSize: 10, color: "#c2410c", fontWeight: 700 }}>Davies-Bouldin</div>
            <div style={{ fontSize: 16, fontWeight: 900, color: "#9a3412" }}>
              {diagnostics.kmeans.davies_bouldin != null ? diagnostics.kmeans.davies_bouldin.toFixed(3) : "N/A"}
            </div>
          </div>
          <div style={{ background: "#ecfeff", borderRadius: 6, padding: 6 }}>
            <div style={{ fontSize: 10, color: "#0e7490", fontWeight: 700 }}>Calinski-Harabasz</div>
            <div style={{ fontSize: 16, fontWeight: 900, color: "#155e75" }}>
              {diagnostics.kmeans.calinski_harabasz != null ? diagnostics.kmeans.calinski_harabasz.toFixed(1) : "N/A"}
            </div>
          </div>
          <div style={{ background: "#fef2f2", borderRadius: 6, padding: 6 }}>
            <div style={{ fontSize: 10, color: "#b91c1c", fontWeight: 700 }}>DBSCAN Noise</div>
            <div style={{ fontSize: 16, fontWeight: 900, color: "#991b1b" }}>
              {(diagnostics.dbscan.noise_ratio * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 6 }}>
        <div style={{ background: "#ffffff", borderRadius: 8, border: "1px solid #e5e7eb", padding: 10, overflow: "hidden" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#1f2937", marginBottom: 8 }}>
            KMeans Segmentation
          </div>
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 8, right: 15, bottom: 30, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Views (log scale)"
                  label={{ value: 'Video Reach (Views Scale)', position: 'bottom', offset: -5, fontSize: 10, fill: '#6b7280' }}
                  stroke="#9ca3af"
                  tick={{ fontSize: 10 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Engagement Rate"
                  label={{ value: 'Engagement %', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#6b7280' }}
                  stroke="#9ca3af"
                  tick={{ fontSize: 10 }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const actualViews = Math.pow(10, data.x);
                      return (
                        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 4, padding: 6, fontSize: 10 }}>
                          <div style={{ fontWeight: 600, marginBottom: 2 }}>{data.title?.substring(0, 40)}...</div>
                          <div style={{ color: '#059669' }}>📊 Views: {actualViews.toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
                          <div style={{ color: '#dc2626' }}>❤️ Engagement: {(data.y * 100).toFixed(2)}%</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: 8, fontSize: 11 }} />
                {series.map((s, i) => (
                  <Scatter
                    key={s.name}
                    name={s.name}
                    data={s.data}
                    fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                    onClick={(p: any) => onSelect(p?.payload?.video_id)}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 6, lineHeight: 1.3 }}>
            📍 X-axis = Video Reach (more views = right) • Y-axis = Engagement Rate (higher = better)
          </div>
        </div>

        <div style={{ background: "#ffffff", borderRadius: 8, border: "1px solid #e5e7eb", padding: 10, overflow: "hidden" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#1f2937", marginBottom: 8 }}>
            DBSCAN Density View
          </div>
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 8, right: 15, bottom: 30, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Views (log scale)"
                  label={{ value: 'Video Reach (Views Scale)', position: 'bottom', offset: -5, fontSize: 10, fill: '#6b7280' }}
                  stroke="#9ca3af"
                  tick={{ fontSize: 10 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Engagement Rate"
                  label={{ value: 'Engagement %', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#6b7280' }}
                  stroke="#9ca3af"
                  tick={{ fontSize: 10 }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const actualViews = Math.pow(10, data.x);
                      return (
                        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 4, padding: 6, fontSize: 10 }}>
                          <div style={{ fontWeight: 600, marginBottom: 2 }}>{data.title?.substring(0, 40)}...</div>
                          <div style={{ color: '#059669' }}>📊 Views: {actualViews.toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
                          <div style={{ color: '#dc2626' }}>❤️ Engagement: {(data.y * 100).toFixed(2)}%</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: 8, fontSize: 11 }} />
                {dbscanSeries.map((s) => (
                  <Scatter
                    key={s.name}
                    name={s.name}
                    data={s.data}
                    fill={s.color}
                    onClick={(p: any) => onSelect(p?.payload?.video_id)}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 6, lineHeight: 1.3 }}>
            🔴 Red = Outliers ({diagnostics ? (diagnostics.dbscan.noise_ratio * 100).toFixed(1) : noisePct.toFixed(1)}%) • 🔵 Blue = Normal pattern
          </div>
        </div>
      </div>

      <div style={{ background: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)", borderRadius: 8, padding: 14, marginTop: 10, border: "1px solid #c7d2fe" }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#1f2937", marginBottom: 10 }}>
          📊 What Each Cluster Means {clusters.length < 4 && <span style={{ fontSize: 11, fontWeight: 400, color: "#6b7280" }}>(showing {clusters.length} of 4 total clusters)</span>}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
          {clusterStats.map(stat => {
            const info = clusterInfo[stat.cluster as keyof typeof clusterInfo];
            if (!info) return null;

            return (
              <div key={stat.cluster} style={{ background: info.bgColor, borderRadius: 6, padding: 10, borderLeft: `3px solid ${info.borderColor}` }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: info.textColor, marginBottom: 3 }}>
                  {info.emoji} Cluster {stat.cluster}: {info.name}
                </div>
                <div style={{ fontSize: 10, color: info.descColor, lineHeight: 1.5 }}>
                  {(stat.avgViews / 1000000).toFixed(1)}M avg views • <strong>{(stat.avgEng * 100).toFixed(2)}% engagement</strong> • {Math.round(stat.avgWatch)}s watch<br/>
                  <span style={{ fontStyle: "italic" }}>→ {info.strategy}</span>
                </div>
              </div>
            );
          })}
        </div>

        {clusters.length < 4 && (
          <div style={{ background: "#fef3c7", borderRadius: 6, padding: 8, marginBottom: 10, border: "1px solid #fbbf24" }}>
            <div style={{ fontSize: 10, color: "#92400e", lineHeight: 1.5 }}>
              ⚠️ <strong>Not all clusters visible:</strong> Some clusters may not appear in this filtered view. Clear filters or increase the video limit to see all 4 performance tiers.
            </div>
          </div>
        )}

        <div style={{ background: "#fff", borderRadius: 6, padding: 10, border: "1px solid #e0e7ff" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#4338ca", marginBottom: 4 }}>Why Two Algorithms?</div>
          <div style={{ fontSize: 10, color: "#6366f1", lineHeight: 1.5 }}>
            <strong>KMeans:</strong> Groups all videos into 4 performance tiers for strategy planning<br/>
            <strong>DBSCAN:</strong> Finds dense patterns and highlights outliers ({diagnostics ? (diagnostics.dbscan.noise_ratio * 100).toFixed(1) : noisePct.toFixed(1)}% unusual videos)
          </div>
        </div>
      </div>
    </div>
  );
}
