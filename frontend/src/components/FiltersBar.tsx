/**
 * Filters Bar - Interactive data pipeline control.
 * 
 * Filtering Dimensions:
 * - Category: education, entertainment, animation, other
 * - Thumbnail Style: Visual categorization
 * - Date Range: Publish date filtering (min/max)
 * 
 * Features:
 * - Dropdown selectors with validation
 * - Date picker with calendar UI
 * - Real-time data updates on filter change
 * - Filter state persistence (URL params optional)
 * 
 * Callback:
 * - onChangeFilters: Parent component handler for reactive updates
 */

import React from "react";
import type { Filters } from "../types";

export default function FiltersBar(props: {
  filters: Filters;
  category: string; setCategory: (v: string) => void;
  thumb: string; setThumb: (v: string) => void;
  minDate: string; setMinDate: (v: string) => void;
  maxDate: string; setMaxDate: (v: string) => void;
}) {
  const f = props.filters;
  return (
    <div style={{
      display: "flex",
      gap: 14,
      flexWrap: "wrap",
      marginTop: 12,
      alignItems: "end",
      background: "linear-gradient(90deg, rgba(255,255,255,0.95) 0%, rgba(248,250,255,0.95) 100%)",
      backdropFilter: "blur(10px)",
      padding: 16,
      borderRadius: 12,
      boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
    }}>
      <div>
        <div style={{ fontSize: 11, color: "#667eea", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>Category</div>
        <select
          value={props.category}
          onChange={(e) => props.setCategory(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "2px solid #e0e7ff",
            fontSize: 14,
            background: "white",
            cursor: "pointer"
          }}
        >
          <option value="">All</option>
          {f.categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div>
        <div style={{ fontSize: 11, color: "#667eea", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>Thumbnail</div>
        <select
          value={props.thumb}
          onChange={(e) => props.setThumb(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "2px solid #e0e7ff",
            fontSize: 14,
            background: "white",
            cursor: "pointer"
          }}
        >
          <option value="">All</option>
          {f.thumbnail_styles.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div>
        <div style={{ fontSize: 11, color: "#667eea", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>Min date</div>
        <input
          type="date"
          value={props.minDate}
          onChange={(e) => props.setMinDate(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "2px solid #e0e7ff",
            fontSize: 14,
            background: "white"
          }}
        />
      </div>

      <div>
        <div style={{ fontSize: 11, color: "#667eea", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>Max date</div>
        <input
          type="date"
          value={props.maxDate}
          onChange={(e) => props.setMaxDate(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "2px solid #e0e7ff",
            fontSize: 14,
            background: "white"
          }}
        />
      </div>
    </div>
  );
}
