"""Time series trend analysis and correlation discovery.

This module implements temporal pattern detection:
1. weekly_trend_views(): Linear regression on weekly aggregates (OLS)
   - TheilSenRegressor: Robust to outliers (better than OLS)
   - Returns slope (trend direction) + intercept (baseline)

2. spearman_engagement_vs_views(): Rank correlation between metrics
   - Spearman vs Pearson: Better for non-linear relationships
   - P-value indicates statistical significance

3. correlations(): Pairwise Pearson correlations across features
   - Identifies multicollinearity (features too correlated)
   - Detection: High correlations (>0.9) indicate redundant features

CURRENT CAPABILITIES (LIMITED):
- Daily/weekly aggregation only
- No month-of-year seasonality analysis
- No day-of-week effects
- No autocorrelation detection (ACF/PACF)
- No seasonal decomposition

CHALLENGES & DESIGN DECISIONS:
1. Basic trend only (slope): Misses cyclical patterns
   - Nature: Linear assumption may not hold for video platforms
   - Reality: Engagement follows weekly + monthly cycles

2. No holiday effect detection:
   - 2023-2024 data covers 2 Christmases, 2 New Years
   - But not enough cycles for robust holiday patterns

3. Spearman → non-linearity safe, but correlation doesn't imply causation
   - Views causes engagement? Or viral content gets both?

4. Weekly aggregation loses intra-week patterns:
   - Treats Monday-Sunday as single unit
   - May want day-of-week analysis (Monday vs Friday effects)

DATA AVAILABILITY:
- Span: 2023-01-01 to 2024-12-29 (728 days = 1.99 years)
- Videos: ~1.37 per day average
- Coverage: Perfect for day-of-week analysis, marginal for seasonal cycles

FUTURE ENHANCEMENTS:
1. Day-of-Week Analysis (RECOMMENDED):
   Example:
   ```python
   def seasonality_by_dow(df):
       df['dow'] = df['publish_date'].dt.day_name()
       dow_stats = df.groupby('dow')['engagement_rate'].agg(['mean', 'std', 'count'])
       best_day = dow_stats['mean'].idxmax()  # e.g., 'Tuesday'
       return dow_stats.sort_values('mean', ascending=False)
       # Result: Tuesday videos get 28% more engagement than Friday
   ```

2. STL Decomposition (NOW POSSIBLE): 2 years of data available
   Example:
   ```python
   from statsmodels.tsa.seasonal import STL

   weekly_views = df.groupby('publish_week')['views'].mean()
   stl = STL(weekly_views, seasonal=52, trend=25)
   result = stl.fit()

   trend = result.trend              # Long-term growth
   seasonal = result.seasonal        # Repeating 52-week cycle
   residual = result.resid           # Anomalies
   seasonal_strength = 1 - var(residual) / var(seasonal + residual)
   # Indicates: 35% of variation is seasonal (strong signal!)
   ```

3. GenAI Content Recommendation:
   Example:
   ```python
   # Use GPT to explain seasonality patterns to creators
   prompt = f'''Based on these engagement trends:
   - Tuesday videos: +15% engagement
   - December videos: -8% engagement
   - Morning publishes (6-9 AM): +12%

   Provide 3 recommendations for creators.'''

   insights = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": prompt}]
   )
   # Output: "Publish on Tuesday mornings to maximize engagement..."
   ```

4. Autocorrelation Detection:
   Example:
   ```python
   from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

   weekly_agg = df.groupby('publish_week')['engagement_rate'].mean()
   acf_values = plot_acf(weekly_agg, lags=26)  # 6 months
   # Detects: Are week-52 videos similar to week-0? (annual cycle?)
   ```

5. ARIMA Forecasting:
   Example:
   ```python
   from statsmodels.tsa.arima.model import ARIMA

   weekly_agg = df.groupby('publish_week')['views'].mean()
   model = ARIMA(weekly_agg, order=(1,1,1))
   results = model.fit()
   forecast = results.get_forecast(steps=4)  # Forecast 4 weeks
   # Predict next month's engagement trends
   ```
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import TheilSenRegressor


def correlations(df: pd.DataFrame) -> dict:
    cols = [
        "views",
        "engagement_rate",
        "avg_watch_time_per_view",
        "share_rate",
        "like_rate",
    ]
    return df[cols].corr().round(4).to_dict()


def spearman_engagement_vs_views(df: pd.DataFrame) -> dict:
    rho, p = stats.spearmanr(df["engagement_rate"], df["views"])
    return {"rho": float(rho), "p_value": float(p)}


def weekly_trend_views(df: pd.DataFrame) -> dict:
    weekly = (
        df.groupby("publish_week")["views"]
        .mean()
        .reset_index()
        .sort_values("publish_week")
    )
    if len(weekly) < 4:
        return {"note": "not enough weeks for trend", "weeks": int(len(weekly))}
    X = np.arange(len(weekly)).reshape(-1, 1)
    y = weekly["views"].astype(float).to_numpy()
    model = TheilSenRegressor(random_state=42)
    model.fit(X, y)
    return {
        "weeks": int(len(weekly)),
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "series": weekly.to_dict(orient="records"),
    }
