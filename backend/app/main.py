"""Content Performance Insights API - FastAPI REST service layer.

This module exposes HTTP endpoints for video performance analytics, including:
- Health checks and API metadata
- Aggregated KPIs (views, engagement metrics)
- Filtering options and video listings
- Complete insights (clustering, predictions, anomalies, trends, recommendations)
- Similar content retrieval via TF-IDF embeddings

The API server initializes application state (models, data, vectorizers) during startup
via the lifespan context manager, ensuring thread-safe singleton access to precomputed artifacts.

Endpoints are CORS-enabled for localhost development. All responses are JSON-serializable
with schema validation via Pydantic models.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .service import build_state, get_similar, insights, overview_metrics
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application state in lifespan handler (startup) and keep it available."""
    # build_state is synchronous and may be moderately heavy; run it here.
    global STATE
    STATE = build_state(
        data_path=settings.data_path,
        cluster_k=settings.cluster_k,
        contamination=settings.anomaly_contamination,
        random_state=settings.random_state,
        test_size=settings.test_size,
        alpha=settings.alpha,
    )
    yield


app = FastAPI(
    title="Content Performance Insights API", version="2.0.0", lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE = None


@app.get("/")
def root():
    return {
        "service": "Content Performance Insights API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/metrics",
            "/filters",
            "/videos",
            "/insights",
            "/similar",
        ],
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    return overview_metrics(STATE.df)


@app.get("/filters")
def filters():
    df = STATE.df
    return {
        "categories": sorted(df["category"].unique().tolist()),
        "thumbnail_styles": sorted(df["thumbnail_style"].unique().tolist()),
        "min_date": df["publish_date"].min().strftime("%Y-%m-%d"),
        "max_date": df["publish_date"].max().strftime("%Y-%m-%d"),
    }


@app.get("/videos")
def videos(
    category: str | None = None,
    thumbnail_style: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    limit: int = Query(default=300, ge=1, le=500),
):
    df = STATE.df
    q = df
    if category:
        q = q[q["category"] == category]
    if thumbnail_style:
        q = q[q["thumbnail_style"] == thumbnail_style]
    if min_date:
        q = q[q["publish_date"] >= min_date]
    if max_date:
        q = q[q["publish_date"] <= max_date]
    q = q.sort_values("views", ascending=False).head(limit)

    out = q[
        [
            "video_id",
            "title",
            "category",
            "publish_date",
            "views",
            "engagement_rate",
            "avg_watch_time_per_view",
            "cluster",
            "dbscan_cluster",
            "is_anomaly",
            "thumbnail_style",
            "engagement_pred",
            "engagement_pi_low",
            "engagement_pi_high",
        ]
    ].copy()
    out["publish_date"] = out["publish_date"].dt.strftime("%Y-%m-%d")
    return out.to_dict(orient="records")


@app.get("/insights")
def insights_endpoint():
    return insights(STATE.df, STATE.predictive)


@app.get("/similar")
def similar(video_id: str, top_k: int = Query(default=8, ge=1, le=20)):
    return get_similar(STATE.df, STATE.tfidf_mat, video_id=video_id, top_k=top_k)
