import json
from pathlib import Path

NB_PATH = Path('notebooks/01_exploration_v2.ipynb')


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find target block for {label}')
    return text.replace(old, new, 1)


nb = json.loads(NB_PATH.read_text())

# Cell indexes: 0-based
c8 = ''.join(nb['cells'][7]['source'])
c10 = ''.join(nb['cells'][9]['source'])
c12 = ''.join(nb['cells'][11]['source'])

# 1) Cell 8: add leakage-safe historical priors
old_c8 = """    # ─ Categorical features ─
    X['category'] = df.get('category', 'unknown').astype(str).fillna('unknown')
    X['thumbnail_style'] = df.get('thumbnail_style', 'unknown').astype(str).fillna('unknown')

    # ─ Title text feature for NLP vectorizers ─
    X['title_raw'] = titles.values
"""
new_c8 = """    # ─ Time progression features (known at publish-time) ─
    days_since_start = (dates - dates.min()).dt.days.fillna(0).astype(float)
    X['time_index_days'] = days_since_start
    X['days_since_prev_upload'] = dates.diff().dt.total_seconds().div(86400).fillna(0).clip(lower=0, upper=365).astype(float)

    # ─ Leakage-safe historical priors from past outcomes only (strictly shifted) ─
    # These are causal at prediction time: each row only uses older rows.
    y = df['engagement_rate'].astype(float)
    y_shift = y.shift(1)
    global_prior = y.expanding().mean().shift(1).fillna(y.mean())

    X['global_er_mean_7'] = y_shift.rolling(7, min_periods=1).mean().fillna(y.mean())
    X['global_er_mean_30'] = y_shift.rolling(30, min_periods=1).mean().fillna(y.mean())

    category = df.get('category', 'unknown').astype(str).fillna('unknown')
    thumbnail = df.get('thumbnail_style', 'unknown').astype(str).fillna('unknown')

    cat_count = y.groupby(category).cumcount()
    cat_sum_past = y.groupby(category).cumsum() - y
    cat_prior = cat_sum_past / cat_count.replace(0, np.nan)
    X['category_er_prior_mean'] = cat_prior.fillna(global_prior)
    X['category_er_prior_count'] = cat_count.astype(float)

    thumb_count = y.groupby(thumbnail).cumcount()
    thumb_sum_past = y.groupby(thumbnail).cumsum() - y
    thumb_prior = thumb_sum_past / thumb_count.replace(0, np.nan)
    X['thumbnail_er_prior_mean'] = thumb_prior.fillna(global_prior)

    pair = category + '||' + thumbnail
    pair_count = y.groupby(pair).cumcount()
    pair_sum_past = y.groupby(pair).cumsum() - y
    pair_prior = pair_sum_past / pair_count.replace(0, np.nan)
    X['category_thumb_er_prior_mean'] = pair_prior.fillna(cat_prior).fillna(global_prior)
    X['category_thumb_er_prior_count'] = pair_count.astype(float)

    # ─ Categorical features ─
    X['category'] = category
    X['thumbnail_style'] = thumbnail

    # ─ Title text feature for NLP vectorizers ─
    X['title_raw'] = titles.values
"""
c8 = _replace_once(c8, old_c8, new_c8, 'cell8 historical priors')

# 2) Cell 10: extend numeric list
old_c10 = """    'question_x_weekend',
]"""
new_c10 = """    'question_x_weekend',
    'time_index_days',
    'days_since_prev_upload',
    'global_er_mean_7',
    'global_er_mean_30',
    'category_er_prior_mean',
    'category_er_prior_count',
    'thumbnail_er_prior_mean',
    'category_thumb_er_prior_mean',
    'category_thumb_er_prior_count',
]"""
c10 = _replace_once(c10, old_c10, new_c10, 'cell10 feature list')

# 3) Cell 12: append rolling-origin backtest
anchor = "print(f\"   Test RMSE:      {best_metrics['rmse']:.6f}\\n\")\n"
if anchor not in c12:
    raise RuntimeError('Could not find insertion anchor in cell12')

extra = """# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Rolling-origin backtest on train+val (scientific validation)
# Tests whether gains are robust vs naive mean under strict temporal CV.
# ═══════════════════════════════════════════════════════════════════════
print('=' * 80)
print('STEP 5: ROLLING-ORIGIN BACKTEST (Train+Val only)')
print('=' * 80)

from sklearn.base import clone

X_hist = pd.concat([X_train, X_val], axis=0).reset_index(drop=True)
y_hist = pd.concat([y_train, y_val], axis=0).reset_index(drop=True)
ts_backtest = TimeSeriesSplit(n_splits=5)

bt_rows = []
for fold_id, (tr_idx, va_idx) in enumerate(ts_backtest.split(X_hist), start=1):
    X_tr_f, X_va_f = X_hist.iloc[tr_idx], X_hist.iloc[va_idx]
    y_tr_f, y_va_f = y_hist.iloc[tr_idx], y_hist.iloc[va_idx]

    fold_model = clone(base_model)
    fold_model.fit(X_tr_f, y_tr_f)
    y_hat_f = fold_model.predict(X_va_f)

    mae_model = float(mean_absolute_error(y_va_f, y_hat_f))
    naive_pred = np.full(len(y_va_f), float(y_tr_f.mean()))
    mae_naive = float(mean_absolute_error(y_va_f, naive_pred))

    bt_rows.append({
        'fold': fold_id,
        'n_train': len(tr_idx),
        'n_val': len(va_idx),
        'mae_model': mae_model,
        'mae_naive_mean': mae_naive,
        'uplift_vs_naive': mae_naive - mae_model,
    })

bt_df = pd.DataFrame(bt_rows)
print(bt_df.to_string(index=False))

mean_uplift = float(bt_df['uplift_vs_naive'].mean())
fold_win_rate = float((bt_df['uplift_vs_naive'] > 0).mean())

rng = np.random.default_rng(42)
uplift_vals = bt_df['uplift_vs_naive'].to_numpy()
boot_means = rng.choice(uplift_vals, size=(5000, len(uplift_vals)), replace=True).mean(axis=1)
ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])

print('\\nBacktest summary:')
print(f'  Mean uplift vs naive MAE: {mean_uplift:.6f}  (positive = better)')
print(f'  95% bootstrap CI:         [{ci_low:.6f}, {ci_high:.6f}]')
print(f'  Fold win rate:            {fold_win_rate*100:.1f}%')

scientific_pass = (mean_uplift > 0) and (ci_low > 0) and (fold_win_rate >= 0.6)
print(f'  Scientific acceptance:    {scientific_pass}')
if not scientific_pass:
    print('  ⚠ Forecastability remains weak under strict temporal backtesting.')

model_metrics['rolling_backtest'] = {
    'mean_uplift_vs_naive_mae': mean_uplift,
    'ci95_low': float(ci_low),
    'ci95_high': float(ci_high),
    'fold_win_rate': fold_win_rate,
    'scientific_pass': bool(scientific_pass),
}
"""
c12 = c12.replace(anchor, anchor + extra, 1)

nb['cells'][7]['source'] = [line + '\n' for line in c8.rstrip('\n').split('\n')]
nb['cells'][9]['source'] = [line + '\n' for line in c10.rstrip('\n').split('\n')]
nb['cells'][11]['source'] = [line + '\n' for line in c12.rstrip('\n').split('\n')]

NB_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print('patched cells 8, 10, 12 to disk')
