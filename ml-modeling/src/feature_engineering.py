"""
feature_engineering.py
Lifecycle-window features for C-MAPSS sensor data.

Design choices (and WHY, for the schema doc handed to Ossama/Hajar):
- Rolling mean & std per sensor over a window of past cycles -> captures
  local degradation trend & noise level, computed causally (no future leakage).
- Rolling slope (linear trend) per sensor over the window -> captures rate
  of degradation, which is more predictive than absolute sensor value.
- Cycle count (current cycle number) -> proxy for "age", helps when sensors
  alone are noisy.
- All features computed per-unit (grouped by 'unit') so no engine's window
  ever crosses into another engine's data.
"""

import numpy as np
import pandas as pd

SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
WINDOW = 5  # cycles look-back window


def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
    """Causal rolling linear-trend slope (least squares) over `window` points."""
    x = np.arange(window)
    x_mean = x.mean()
    denom = ((x - x_mean) ** 2).sum()

    def slope_fn(y):
        if len(y) < window:
            return np.nan
        y_mean = y.mean()
        return ((x - x_mean) * (y - y_mean)).sum() / denom

    return series.rolling(window).apply(slope_fn, raw=True)


def add_window_features(df: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    """
    Add rolling mean / std / slope per sensor, computed causally within each unit.
    First `window-1` rows per unit will have NaN -> dropped by caller if needed.
    """
    df = df.sort_values(["unit", "cycle"]).copy()
    grouped = df.groupby("unit")

    feature_frames = [df]
    for col in SENSOR_COLS:
        roll = grouped[col].rolling(window)
        mean_feat = roll.mean().reset_index(level=0, drop=True)
        std_feat = roll.std().reset_index(level=0, drop=True)
        slope_feat = grouped[col].transform(lambda s: _rolling_slope(s, window))

        feature_frames.append(mean_feat.rename(f"{col}_roll_mean"))
        feature_frames.append(std_feat.rename(f"{col}_roll_std"))
        feature_frames.append(slope_feat.rename(f"{col}_roll_slope"))

    out = pd.concat(feature_frames, axis=1)
    return out


def get_feature_columns(window_cols=True):
    base = [f"op_setting_{i}" for i in (1, 2, 3)] + SENSOR_COLS + ["cycle"]
    if not window_cols:
        return base
    window_feats = []
    for col in SENSOR_COLS:
        window_feats += [f"{col}_roll_mean", f"{col}_roll_std", f"{col}_roll_slope"]
    return base + window_feats


if __name__ == "__main__":
    from data_loader import load_dataset

    train, test = load_dataset("data/raw", "FD001")
    train_feat = add_window_features(train)
    print("Shape before:", train.shape, "after:", train_feat.shape)
    print("NaN rows (warm-up period per engine):", train_feat["sensor_2_roll_mean"].isna().sum())
    print(train_feat[["unit", "cycle", "sensor_2", "sensor_2_roll_mean",
                       "sensor_2_roll_std", "sensor_2_roll_slope"]].head(8))
