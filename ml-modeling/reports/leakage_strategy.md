# Train/Test Split Strategy — Leakage Avoidance

NASA C-MAPSS already gives separate train/test engine units (no shared units
between train and test), so the main leakage risks are not "row splitting" but
these three:

1. **Splitting by row instead of by unit for validation.**
   - WRONG: random row-level train/val split. Rows from the same engine's
     trajectory end up in both sets -> model memorizes that engine's specific
     curve -> leakage.
   - RIGHT: split by `unit` id. We hold out ~20% of TRAIN units entirely for
     validation (`GroupKFold` / manual unit-based split), never mixing cycles
     from the same engine across folds.

2. **Feature engineering using future cycles.**
   - WRONG: a rolling average that looks both forward and backward in time.
   - RIGHT: all rolling/window features use only past+current cycles
     (`rolling(window).mean()` with no `center=True`, no shifting backwards).

3. **Fitting scalers/normalizers on train+test combined.**
   - WRONG: `StandardScaler().fit(pd.concat([train, test]))`.
   - RIGHT: fit scaler ONLY on train units, then `.transform()` test.

4. **RUL clipping threshold chosen by looking at test performance.**
   - We fix the clip value (125, standard in C-MAPSS literature) before
     touching test data, based on train distribution only.

Validation scheme used: `GroupKFold(n_splits=5, groups=train_df['unit'])`
via scikit-learn, so cross-validation respects unit boundaries.