import React, { useEffect, useMemo, useState } from "react";
import { getJson } from "./api/client";
import type { Filters, Metrics, SimilarRow, VideoRow, Insights } from "./types";
import Overview from "./components/Overview";
import FiltersBar from "./components/FiltersBar";
import ClusterScatter from "./components/ClusterScatter";
import AnomaliesTable from "./components/AnomaliesTable";
import SimilarPanel from "./components/SimilarPanel";
import PredictivePanel from "./components/PredictivePanel";

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [filters, setFilters] = useState<Filters | null>(null);
  const [rows, setRows] = useState<VideoRow[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);

  const [category, setCategory] = useState("");
  const [thumb, setThumb] = useState("");
  const [minDate, setMinDate] = useState("");
  const [maxDate, setMaxDate] = useState("");
  const [selected, setSelected] = useState<string>("");
  const [similar, setSimilar] = useState<SimilarRow[]>([]);

  const anomalies = useMemo(() => rows.filter(r => r.is_anomaly), [rows]);

  useEffect(() => {
    (async () => {
      const [m, f, i] = await Promise.all([
        getJson<Metrics>("/metrics"),
        getJson<Filters>("/filters"),
        getJson<any>("/insights")
      ]);
      setMetrics(m);
      setFilters(f);
      setInsights(i as Insights);
      setMinDate(f.min_date);
      setMaxDate(f.max_date);
    })().catch(console.error);
  }, []);

  useEffect(() => {
    (async () => {
      const qs = new URLSearchParams();
      if (category) qs.set("category", category);
      if (thumb) qs.set("thumbnail_style", thumb);
      if (minDate) qs.set("min_date", minDate);
      if (maxDate) qs.set("max_date", maxDate);
      qs.set("limit", "300");
      const v = await getJson<VideoRow[]>(`/videos?${qs.toString()}`);
      setRows(v);
      setSelected(prev => prev || v[0]?.video_id || "");
    })().catch(console.error);
  }, [category, thumb, minDate, maxDate]);

  useEffect(() => {
    (async () => {
      if (!selected) return;
      const s = await getJson<SimilarRow[]>(`/similar?video_id=${encodeURIComponent(selected)}&top_k=8`);
      setSimilar(s);
    })().catch(console.error);
  }, [selected]);

  return (
    <div style={{
      fontFamily: "system-ui",
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: 16
    }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", paddingBottom: 24 }}>
      <h1 style={{ margin: "0 0 6px 0", color: "#fff", fontSize: 36, fontWeight: 800, textShadow: "2px 2px 4px rgba(0,0,0,0.2)" }}>
        Content Performance Insights Dashboard
      </h1>
      <div style={{ color: "#f0f0f0", marginBottom: 16, fontSize: 14 }}>
        ETL + clustering + trend detection + embeddings + anomaly detection + prediction + MAPIE Jackknife+ conformal intervals.
      </div>

      {metrics && <Overview metrics={metrics} />}

      {filters && (
        <FiltersBar
          filters={filters}
          category={category} setCategory={setCategory}
          thumb={thumb} setThumb={setThumb}
          minDate={minDate} setMinDate={setMinDate}
          maxDate={maxDate} setMaxDate={setMaxDate}
        />
      )}

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginTop: 16 }}>
        <div style={{
          background: "linear-gradient(135deg, #fff 0%, #f8f9ff 100%)",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          border: "1px solid rgba(255,255,255,0.3)"
        }}>
          <h2 style={{ marginTop: 0, marginBottom: 8 }}>Content Clustering Analysis</h2>
          <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
            KMeans (4 Performance Tiers) + DBSCAN (Density Detection)
          </div>
          <ClusterScatter rows={rows} onSelect={setSelected} diagnostics={insights?.clustering_diagnostics} />
        </div>
        <div style={{
          background: "linear-gradient(135deg, #fff 0%, #fff8f0 100%)",
          borderRadius: 16,
          padding: 20,
          boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          border: "1px solid rgba(255,255,255,0.3)"
        }}>
          <h2 style={{ marginTop: 0 }}>Similar Titles (TF‑IDF)</h2>
          <SimilarPanel rows={rows} selected={selected} setSelected={setSelected} similar={similar} />
        </div>
      </div>

      <div style={{
        marginTop: 16,
        background: "linear-gradient(135deg, #fff 0%, #f0fff8 100%)",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
        border: "1px solid rgba(255,255,255,0.3)"
      }}>
        <h2 style={{ marginTop: 0 }}>Anomalies (IsolationForest)</h2>
        <AnomaliesTable rows={anomalies} />
      </div>

      <div style={{
        marginTop: 16,
        background: "linear-gradient(135deg, #fff 0%, #fff0fa 100%)",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
        border: "1px solid rgba(255,255,255,0.3)"
      }}>
        <h2 style={{ marginTop: 0 }}>Predictive Model + MAPIE Jackknife+ Intervals</h2>
        <PredictivePanel rows={rows} insights={insights} />
      </div>
      </div>
    </div>
  );
}
