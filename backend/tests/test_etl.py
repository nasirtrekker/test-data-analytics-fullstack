import pandas as pd
import tempfile
from app.etl import load_clean

def test_derived_metrics():
    df = pd.DataFrame([{
        "video_id":"001","title":"t","category":"c","publish_date":"2024-01-01",
        "views":100,"watch_time_seconds":1000,"likes":10,"comments":5,"shares":2,"thumbnail_style":"x"
    }])
    with tempfile.NamedTemporaryFile(suffix=".csv") as f:
        df.to_csv(f.name, index=False)
        out = load_clean(f.name)
        assert abs(out.loc[0,"engagement_rate"] - 0.17) < 1e-9
        assert abs(out.loc[0,"avg_watch_time_per_view"] - 10.0) < 1e-9
