# Dual-Split Strategy: Video-ID + Temporal Ordering

## Overview

The predictive model uses a **dual-split strategy** to prevent ALL types of leakage:

1. **Video-ID Grouping**: No same video_id appears in train/val/test splits
2. **Temporal Ordering**: Videos ordered chronologically (2023 → train, 2024-early → val, 2024-late → test)

This ensures:
- ✅ No data leakage via duplicate videos across folds
- ✅ No look-ahead bias via chronological ordering
- ✅ Realistic deployment scenario (predict future using past)

---

## Dataset Structure

```
Total videos: 1000 (each with unique video_id)
Observations per video: 1 (NOT time-series/longitudinal)
Temporal range: 2023-01-01 to 2024-12-29

Dataset = {video_id, title, category, publish_date, views, likes, comments, shares, thumbnail_style, watch_time_seconds}
```

**Key property**: Each video_id appears exactly once (no duplicates)

---

## Split Implementation

### Notebook Approach (01_exploration_v2.ipynb | Cell 8)

```python
# 1. Sort by chronological order
dates = pd.to_datetime(df['publish_date'])
order = dates.sort_values(kind='mergesort').index
df = df.loc[order].reset_index(drop=True)

# 2. Get unique video_ids in temporal order
unique_video_ids = df.drop_duplicates(subset=['video_id'], keep='first')['video_id'].values
# Result: 1000 videos in chronological order

# 3. Split video_ids (not rows) into train/val/test
n_videos = len(unique_video_ids)  # 1000
n_train_videos = int(n_videos * 0.6)  # 600
n_val_videos = int(n_videos * 0.2)  # 200
n_test_videos = n_videos - n_train_videos - n_val_videos  # 200

train_video_ids = set(unique_video_ids[:n_train_videos])
val_video_ids = set(unique_video_ids[n_train_videos:n_train_videos + n_val_videos])
test_video_ids = set(unique_video_ids[n_train_videos + n_val_videos:])

# 4. Assign rows based on video_id membership
X_train = X_full[df['video_id'].isin(train_video_ids)]
X_val = X_full[df['video_id'].isin(val_video_ids)]
X_test = X_full[df['video_id'].isin(test_video_ids)]

# 5. Verify no leakage
assert len(train_video_ids & val_video_ids) == 0  # ✅ No overlap
assert len(train_video_ids & test_video_ids) == 0  # ✅ No overlap
assert len(val_video_ids & test_video_ids) == 0  # ✅ No overlap
```

**Result**:
```
Train split:
  Video IDs: 600 unique
  Rows: 600 samples
  Date range: 2023-01-01 to 2024-03-16

Val split:
  Video IDs: 200 unique
  Rows: 200 samples
  Date range: 2024-03-17 to 2024-08-04

Test split:
  Video IDs: 200 unique  
  Rows: 200 samples
  Date range: 2024-08-04 to 2024-12-29

✅ NO LEAKAGE — Zero video_id overlaps
```

### Backend Approach (backend/app/analysis_predictive.py)

New function `_videoid_temporal_split()`:

```python
def _videoid_temporal_split(
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
    video_ids: pd.Series,
    test_size: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split by video_id groups + temporal ordering.
    
    Prevents TWO types of leakage:
    1. Same video_id doesn't appear in multiple folds
    2. Temporal ordering preserved: old→train, new→test
    """
    # Sort by date
    order = dates.sort_values(kind='mergesort').index
    Xo = X.loc[order].reset_index(drop=True)
    yo = y.loc[order].reset_index(drop=True)
    video_ids_o = video_ids.loc[order].reset_index(drop=True)
    
    # Get unique video_ids in temporal order
    unique_ids = video_ids_o.drop_duplicates().values
    n_videos = len(unique_ids)
    
    # Split based on video_id count
    n_test_videos = max(1, int(round(n_videos * test_size)))
    split_point = n_videos - n_test_videos
    
    train_ids = set(unique_ids[:split_point])
    test_ids = set(unique_ids[split_point:])
    
    # Assign rows by video_id membership
    train_mask = video_ids_o.isin(train_ids)
    test_mask = video_ids_o.isin(test_ids)
    
    return (
        Xo[train_mask].reset_index(drop=True),
        Xo[test_mask].reset_index(drop=True),
        yo[train_mask].reset_index(drop=True),
        yo[test_mask].reset_index(drop=True),
    )
```

Used in `fit_predictive_with_conformal()`:

```python
X_train, X_test, y_train, y_test = _videoid_temporal_split(
    X=X, 
    y=y, 
    dates=valid_dates, 
    video_ids=video_ids, 
    test_size=test_size
)
```

---

## Why This Strategy?

| Leakage Type | Problem | Our Solution |
|---|---|---|
| **Duplicate video** | Same video in train AND test | Video-ID grouping ✅ |
| **Look-ahead bias** | Test uses earlier data than train | Temporal ordering ✅ |
| **Engagement metrics** | Features include components of target | Pre-pub features only ✅ |

---

## Honest Model Results

With dual-split strategy:

```
Best Model: Tuned XGBoost (temporal + video-ID split)
Test R²:    -0.0007  (essentially ZERO)
Test MAE:   0.010689
Test RMSE:  0.012690

Conformal Prediction:
  Target coverage: 90%
  Actual coverage: 93% ✅
  qhat: 0.019873
```

**Interpretation**: 
- Pre-publication features alone **cannot predict engagement**
- Engagement depends on post-publication factors (recommendations, virality, etc.)
- Low/negative R² is **correct**, not a failure

---

## When to Use This Strategy

**Use video-ID + temporal split when:**
- ✅ Each entity (video, user, product) appears 0-1 times in dataset
- ✅ Forecasting scenario (predict future from past)
- ✅ Temporal trends matter
- ✅ Want strictest leakage prevention

**Use temporal split alone when:**
- ✅ Time-series data (multiple observations per entity)
- ✅ Cross-section available for each time point

**Use random/grouped k-fold when:**
- ✅ No temporal structure
- ✅ No entity duplication risk
- ✅ Simple independent predictions

---

## Deployment Implications

**In production**, when a new video is published:

1. **At decision time** (within 24h of publish):
   - ✅ Available: title, category, publish_date, thumbnail_style
   - ❌ NOT available: likes, comments, shares, views

2. **Model input** (ONLY pre-publication):
   ```python
   X_prod = engineer_features_prepub_only(video_data)
   # Features: title_length, category, month_sin, etc.
   # NO engagement metrics
   ```

3. **Prediction + Uncertainty**:
   ```python
   pred, pi_low, pi_high = model.predict_with_intervals(X_prod)
   # pred ≈ 0.044 (engagement_rate)
   # interval: [0.025, 0.063] (90% coverage)
   ```

**Key**: Model deployment uses SAME features as training → no domain shift

---

## Verification Checklist

- [x] No duplicate video_ids in dataset (verified: 1000 unique/1000 total)
- [x] Train/val/test video_ids have zero overlap
- [x] Chronological ordering: 2023 → 2024-03 → 2024-08 → 2024-12
- [x] Pre-publication features only (no engagement metrics)
- [x] Backend tests passing (2/2)
- [x] Conformal intervals achieve target coverage
- [x] Honest R²≈0 (correct for weak signal)

---

## References

- **Notebook:** [01_exploration_v2.ipynb](../notebooks/01_exploration_v2.ipynb) - Cell 8 (dual-split implementation)
- **Backend:** [analysis_predictive.py](../backend/app/analysis_predictive.py) - `_videoid_temporal_split()` function
- **Documentation:** [LEAKAGE_FIX_AND_HONEST_APPROACH.md](./LEAKAGE_FIX_AND_HONEST_APPROACH.md) - Full journey

