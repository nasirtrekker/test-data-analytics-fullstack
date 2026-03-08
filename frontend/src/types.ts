export type Metrics = {
  rows: number;
  total_views: number;
  avg_engagement_rate: number;
  avg_watch_time_per_view: number;
  cluster_count: number;
  dbscan_cluster_count: number;
  dbscan_noise_count: number;
  anomaly_count: number;
};

export type Filters = {
  categories: string[];
  thumbnail_styles: string[];
  min_date: string;
  max_date: string;
};

export type VideoRow = {
  video_id: string;
  title: string;
  category: string;
  publish_date: string;
  views: number;
  engagement_rate: number;
  avg_watch_time_per_view: number;
  cluster: number;
  dbscan_cluster: number;
  is_anomaly: boolean;
  thumbnail_style: string;
  engagement_pred: number;
  engagement_pi_low: number;
  engagement_pi_high: number;
};

export type SimilarRow = {
  video_id: string;
  title: string;
  similarity: number;
  views: number;
  engagement_rate: number;
};

export type Insights = {
  clustering_diagnostics?: {
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
  predictive_model: {
    metrics: { mae: number; r2: number; coverage: number; qhat: number; alpha: number; method?: string };
    top_feature_importances: { feature: string; importance: number }[];
    diagnostics?: {
      points: {
        index: number;
        actual: number;
        predicted: number;
        residual: number;
        pi_low: number;
        pi_high: number;
      }[];
      residual_histogram: {
        bin_left: number;
        bin_right: number;
        count: number;
      }[];
    };
    shap_summary?: {
      available: boolean;
      top_features: {
        feature: string;
        mean_abs_shap: number;
      }[];
      feature_order?: string[];
      beeswarm_points?: {
        feature: string;
        feature_rank: number;
        sample_index: number;
        shap_value: number;
        feature_value: number;
        feature_value_norm: number;
        jitter: number;
      }[];
    };
  };
};
