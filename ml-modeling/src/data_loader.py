"""
data_loader.py
Loads NASA C-MAPSS turbofan degradation data and computes RUL labels.

NASA target definition:
- Each unit (engine) runs from cycle 1 until failure (last cycle in train data).
- Train data has NO RUL column -> RUL(t) = max_cycle(unit) - t  (true RUL for training).
- Test data is truncated BEFORE failure -> true RUL is given separately in RUL_FDxxx.txt,
  and represents the remaining cycles AFTER the last recorded cycle in the test file.
"""

import pandas as pd
from pathlib import Path

# Column names per NASA C-MAPSS documentation
COLS = (
    ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def load_raw(filepath: str) -> pd.DataFrame:
    """Load a raw train_*.txt or test_*.txt file (whitespace separated, no header)."""
    df = pd.read_csv(filepath, sep=r"\s+", header=None)
    df = df.iloc[:, : len(COLS)]  # drop trailing NaN columns from double spaces
    df.columns = COLS
    return df


def add_rul_train(df: pd.DataFrame) -> pd.DataFrame:
    """Add RUL column to TRAINING data: RUL = max_cycle(unit) - current_cycle."""
    max_cycle = df.groupby("unit")["cycle"].transform("max")
    df = df.copy()
    df["RUL"] = max_cycle - df["cycle"]
    return df


def add_rul_test(df: pd.DataFrame, rul_file: str) -> pd.DataFrame:
    """
    Add RUL column to TEST data.
    rul_file contains, per unit, the true remaining cycles AFTER the last
    recorded cycle in the test set. We add that offset to compute RUL at every
    timestep the same way as training data.
    """
    true_rul = pd.read_csv(rul_file, sep=r"\s+", header=None).iloc[:, 0]
    true_rul.index = true_rul.index + 1  # unit ids are 1-indexed
    df = df.copy()
    max_cycle_per_unit = df.groupby("unit")["cycle"].max()
    # final RUL at last observed cycle = true_rul; so total "virtual max cycle"
    # = last observed cycle + true_rul
    virtual_max_cycle = max_cycle_per_unit + true_rul
    df["RUL"] = df["unit"].map(virtual_max_cycle) - df["cycle"]
    return df


def load_dataset(data_dir: str, subset: str = "FD001"):
    """
    Load train/test/RUL for a given subset (FD001..FD004), with RUL columns added.
    Returns: train_df, test_df
    """
    data_dir = Path(data_dir)
    train = load_raw(data_dir / f"train_{subset}.txt")
    test = load_raw(data_dir / f"test_{subset}.txt")
    rul_file = data_dir / f"RUL_{subset}.txt"

    train = add_rul_train(train)
    test = add_rul_test(test, rul_file)
    return train, test


if __name__ == "__main__":
    train, test = load_dataset("data/raw", "FD001")
    print("Train shape:", train.shape)
    print("Test shape:", test.shape)
    print(train.head())
    print("\nRUL stats (train):")
    print(train["RUL"].describe())