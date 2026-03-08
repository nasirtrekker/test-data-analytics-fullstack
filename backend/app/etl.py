from __future__ import annotations

import pandas as pd

REQUIRED = [
    "video_id",
    "title",
    "category",
    "publish_date",
    "views",
    "watch_time_seconds",
    "likes",
    "comments",
    "shares",
    "thumbnail_style",
]


class DataError(ValueError):
    pass


def load_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataError(f"Missing columns: {missing}")

    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    for c in ["views", "watch_time_seconds", "likes", "comments", "shares"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=REQUIRED)
    df = df[(df["views"] > 0) & (df["watch_time_seconds"] >= 0)]
    df = df[(df["likes"] >= 0) & (df["comments"] >= 0) & (df["shares"] >= 0)]

    df["engagement_rate"] = (df["likes"] + df["comments"] + df["shares"]) / df["views"]
    df["avg_watch_time_per_view"] = df["watch_time_seconds"] / df["views"]
    df["like_rate"] = df["likes"] / df["views"]
    df["comment_rate"] = df["comments"] / df["views"]
    df["share_rate"] = df["shares"] / df["views"]

    df["publish_week"] = df["publish_date"].dt.to_period("W").astype(str)
    df["publish_year"] = df["publish_date"].dt.year
    df["publish_month"] = df["publish_date"].dt.month
    df["publish_weekday"] = df["publish_date"].dt.weekday

    title = df["title"].astype(str)
    df["title_length"] = title.str.len()
    df["title_words"] = title.str.split().str.len()

    return df.reset_index(drop=True)
