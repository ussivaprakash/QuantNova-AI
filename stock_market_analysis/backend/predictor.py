"""
Stage 4: Prediction Model Module.
Trains a Random Forest Classifier to predict whether tomorrow's closing price
will be higher than today's (1 or 0) using strictly historical past features.

Performs chronological train-test split and reports:
- Accuracy, Precision, Recall, F1 Score
- Confusion Matrix (TN, FP, FN, TP)
- Feature Importance ranking
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


def build_prediction_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Feature engineering for Random Forest Model.
    Target: 1 if tomorrow's Close > today's Close, else 0.
    All features use strictly past data (lagged/current indicator values).
    """
    data = df.copy()

    # Target: 1 if Close(t+1) > Close(t), else 0
    data["Target"] = (data["Close"].shift(-1) > data["Close"]).astype(int)

    # Historical past feature columns
    data["Price_to_SMA20"] = data["Close"] / data["20-Day MA"] - 1.0
    data["Price_to_SMA50"] = data["Close"] / data["50-Day MA"] - 1.0
    data["SMA20_to_SMA50"] = data["20-Day MA"] / data["50-Day MA"] - 1.0
    data["RSI_Norm"] = data["RSI (14)"] / 100.0
    data["MACD_Norm"] = data["MACD Histogram"] / data["Close"]
    data["BB_%B"] = data["BB %B"]
    data["Vol_Change"] = data["Volume Change (%)"] / 100.0
    data["Return_1D"] = data["Daily Return (%)"] / 100.0
    data["Return_5D"] = data["Close"].pct_change(5)
    data["ATR_Norm"] = data["ATR (14)"] / data["Close"]
    data["ADX_Norm"] = data["ADX (14)"] / 100.0
    data["Gap_Up_Flag"] = data["Gap Up"].astype(int)
    data["Gap_Down_Flag"] = data["Gap Down"].astype(int)

    feature_cols = [
        "Price_to_SMA20",
        "Price_to_SMA50",
        "SMA20_to_SMA50",
        "RSI_Norm",
        "MACD_Norm",
        "BB_%B",
        "Vol_Change",
        "Return_1D",
        "Return_5D",
        "ATR_Norm",
        "ADX_Norm",
        "Gap_Up_Flag",
        "Gap_Down_Flag",
    ]

    # Clean missing/infinite values
    data[feature_cols] = data[feature_cols].replace([np.inf, -np.inf], np.nan)
    valid_data = data.dropna(subset=feature_cols + ["Target"]).copy()

    # Clip outliers
    for col in feature_cols:
        valid_data[col] = valid_data[col].clip(lower=-10.0, upper=10.0)

    X = valid_data[feature_cols]
    y = valid_data["Target"]

    return X, y, valid_data


def train_and_evaluate_random_forest(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Trains Random Forest Classifier using chronological train-test split (70% Train, 30% Test).
    Returns:
      - df_with_predictions: Original DataFrame augmented with probabilities and predictions.
      - metrics: Dictionary containing Accuracy, Precision, Recall, F1 Score, Confusion Matrix.
      - feature_importance_df: DataFrame of feature importances sorted in descending order.
    """
    X, y, valid_df = build_prediction_features(df)

    if len(X) < 40:
        # Fallback if dataset is very small
        res = df.copy()
        res["ML Bull Prob (%)"] = 50.0
        res["ML Prediction"] = "Neutral (Insufficient Data)"
        res["ML Confidence"] = "Low"
        return res, {}, pd.DataFrame()

    # Chronological Split (70% Train, 30% Test)
    split_idx = int(len(X) * 0.70)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        min_samples_split=5,
        random_state=42
    )
    rf_model.fit(X_train_scaled, y_train)

    # Out-of-sample predictions on Test Set
    y_pred = rf_model.predict(X_test_scaled)
    y_prob = rf_model.predict_proba(X_test_scaled)[:, 1]

    # Calculate Performance Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    metrics = {
        "Train Samples": len(X_train),
        "Test Samples": len(X_test),
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1 Score": round(f1, 4),
        "True Positives (TP)": int(tp),
        "False Positives (FP)": int(fp),
        "True Negatives (TN)": int(tn),
        "False Negatives (FN)": int(fn),
    }

    # Feature Importance Breakdown
    importances = rf_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        "Feature": X.columns,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False).reset_index(drop=True)

    # Full Dataset Predictions for Downstream Signal Engine
    X_all_scaled = scaler.transform(X)
    all_probs = rf_model.predict_proba(X_all_scaled)[:, 1] * 100.0

    res = df.copy()
    res["ML Bull Prob (%)"] = 50.0
    res["ML Prediction"] = "Neutral / Mixed"
    res["ML Confidence"] = "Low"

    for i, orig_idx in enumerate(valid_df.index):
        prob = round(all_probs[i], 2)
        res.loc[orig_idx, "ML Bull Prob (%)"] = prob
        if prob >= 60.0:
            res.loc[orig_idx, "ML Prediction"] = "Bullish Forecast"
            res.loc[orig_idx, "ML Confidence"] = "High" if prob >= 70.0 else "Moderate"
        elif prob <= 40.0:
            res.loc[orig_idx, "ML Prediction"] = "Bearish Forecast"
            res.loc[orig_idx, "ML Confidence"] = "High" if prob <= 30.0 else "Moderate"
        else:
            res.loc[orig_idx, "ML Prediction"] = "Neutral / Mixed"
            res.loc[orig_idx, "ML Confidence"] = "Low"

    return res, metrics, feature_importance_df
