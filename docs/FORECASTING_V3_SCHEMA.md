# Forecasting V3 Data Schema and Plan

## Why V3

Current data is one snapshot per video and does not include the exogenous or early-window telemetry needed for strong pre-publication forecasting.

V3 introduces a causal feature set and targets that are learnable in production.

## Modeling Objective

Primary objective:
- Predict 24h engagement proxy from pre-publish + launch-window telemetry.

Secondary objective:
- Predict 48h uplift from 24h signals.

Fallback objective:
- Classification/ranking (`top_quartile_engagement_24h`) when regression signal is weak.

## Required Tables

## `videos`

One row per video metadata.

Columns:
- `video_id` (string, PK)
- `creator_id` (string)
- `publish_ts_utc` (timestamp)
- `platform` (enum)
- `category` (string)
- `thumbnail_style` (string)
- `title_raw` (string)
- `title_lang` (string, optional)

## `creator_daily`

Creator history features available at publish time.

Columns:
- `creator_id` (string)
- `as_of_date` (date)
- `subscribers` (int)
- `videos_last_30d` (int)
- `creator_er_mean_30d` (float)
- `creator_views_mean_30d` (float)
- `creator_watch_time_mean_30d` (float)

Keys:
- (`creator_id`, `as_of_date`)

## `video_window_metrics`

Event-window telemetry.

Columns:
- `video_id` (string)
- `window_end_hours` (int; allowed: 1, 6, 24, 48)
- `impressions` (int)
- `views` (int)
- `watch_time_seconds` (float)
- `likes` (int)
- `comments` (int)
- `shares` (int)
- `traffic_reco_share` (float)
- `traffic_search_share` (float)
- `traffic_external_share` (float)
- `device_mobile_share` (float)

Keys:
- (`video_id`, `window_end_hours`)

## `video_targets`

Training targets produced after observation windows close.

Columns:
- `video_id` (string)
- `engagement_rate_24h` (float)
- `engagement_rate_48h` (float)
- `uplift_24h_to_48h` (float)
- `top_quartile_24h` (bool)

## Feature Contract by Prediction Time

At publish time (t=0):
- Allowed: `videos` + lagged `creator_daily` + calendar/title features.
- Forbidden: any post-publish metrics.

At t=1h or t=6h updates:
- Allowed: same as above + `video_window_metrics` up to current window.
- Forbidden: future windows (no 24h data when predicting 24h at t=1h).

## Evaluation Protocol

Use strict temporal splits:
- Train: oldest range
- Validation: middle range
- Test: newest range

Acceptance gates:
- Regression:
  - `mae_uplift_vs_naive > 0`
  - `abs(coverage - target_coverage) <= 0.05`
  - rolling-origin win-rate >= 0.60
- Classification/ranking:
  - PR-AUC uplift over baseline
  - calibration error within threshold

If gates fail, report `low_forecastability_regime=true`.

## Minimal Implementation Steps

1. Add ingestion for `video_window_metrics` and `creator_daily`.
2. Build point-in-time feature builder with strict cutoff timestamp.
3. Train two models:
   - Regression (`engagement_rate_24h`)
   - Classification (`top_quartile_24h`)
4. Keep conformal intervals for regression output.
5. Expose benchmark mode in API/UI:
   - model vs naive metrics
   - acceptance status

## Notes

- Never train on synthetic early counts unless the same generation process is guaranteed in production.
- Keep leakage guards in code for forbidden post-outcome columns.