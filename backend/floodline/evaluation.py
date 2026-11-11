"""Temporal/event evaluation; synthetic experiments cannot promote a live model."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, fbeta_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import ROOT, stamp, utc
from .data import fingerprint
from .prediction import RULE_VERSION

FEATURES = ["rainfall_1h_mm", "rainfall_3h_mm", "relative_elevation_m", "impervious_fraction", "drainage_constraint", "water_level_m"]
SEED = 20261111


def create_synthetic_experiment(path: Path):
    rng = random.Random(SEED)
    rows = []
    start = datetime(2026, 8, 1, 6, tzinfo=timezone.utc)
    for event in range(18):
        storm = rng.uniform(0, 1)
        base = start + timedelta(days=event * 3)
        for column in range(3):
            for area in range(3):
                drainage, impervious = 0.2 + column * 0.25, 0.35 + column * 0.15 + area * 0.04
                rain = max(0, storm * 120 + rng.gauss(0, 15))
                latent = .055 * (rain - 70) + 1.1 * drainage + .5 * impervious - .5 + rng.gauss(0, .7)
                flooded = int(rng.random() < 1 / (1 + math.exp(-latent)))
                for offset in [0, 45, 90, 135]:
                    issue = base + timedelta(minutes=offset)
                    unknown = rng.random() < .035
                    row = {"row_id": f"s{event + 1}-{column}-{area}-{offset}", "event_id": f"synthetic-storm-{event + 1:02d}",
                           "area_id": f"{chr(65 + column)}{area + 1}", "issued_at": stamp(issue),
                           "available_at": stamp(issue - timedelta(minutes=2)), "label_window_end": stamp(issue + timedelta(hours=3)),
                           "onset": stamp(base + timedelta(minutes=165)) if flooded else "", "data_mode": "synthetic",
                           "label_state": "unknown" if unknown else "synthetic", "label": "" if unknown else flooded,
                           "evidence_reference": "Project-authored simulator; no field observation", "negative_supported": int(not flooded),
                           "rainfall_1h_mm": round(max(0, rain / 3 + rng.gauss(0, 3)), 2),
                           "rainfall_3h_mm": round(max(0, rain + rng.gauss(0, 6)), 2), "relative_elevation_m": 8 - column * 2 - area * .5,
                           "impervious_fraction": impervious, "drainage_constraint": drainage,
                           "water_level_m": "" if rng.random() < .08 else round(2 + storm * 3 + rng.gauss(0, .3), 2)}
                    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def eligible_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"row_id", "event_id", "area_id", "issued_at", "available_at", "label_window_end", "data_mode", "label_state", "label", "evidence_reference", "negative_supported", *FEATURES}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Evaluation CSV is empty or missing documented evidence/feature columns.")
    usable, exclusions = [], {"unknown_label": 0, "unsupported_negative": 0, "unverified_label": 0, "late_features": 0}
    modes = {row["data_mode"] for row in rows}
    if len(modes) != 1 or not modes.issubset({"synthetic", "real"}):
        raise ValueError("Real and synthetic evaluation data must be supplied as separate datasets.")
    mode = next(iter(modes))
    seen = set()
    for row in rows:
        if row["row_id"] in seen:
            raise ValueError("Evaluation row IDs must be unique.")
        seen.add(row["row_id"])
        if utc(row["available_at"]) > utc(row["issued_at"]):
            exclusions["late_features"] += 1
            continue
        if utc(row["label_window_end"]) != utc(row["issued_at"]) + timedelta(hours=3):
            raise ValueError("Each target window must end exactly three hours after issue time.")
        if row["label_state"] == "unknown" or row["label"] not in ("0", "1"):
            exclusions["unknown_label"] += 1
            continue
        if not row["evidence_reference"] or (mode == "real" and row["label_state"] not in ("positive", "negative")):
            exclusions["unverified_label"] += 1
            continue
        if row["label"] == "0" and row["negative_supported"] != "1":
            exclusions["unsupported_negative"] += 1
            continue
        if mode == "real" and ((row["label_state"] == "positive") != (row["label"] == "1")):
            raise ValueError("Positive/negative label state conflicts with the target value.")
        if row["label"] == "1" and row.get("onset") and not (utc(row["issued_at"]) < utc(row["onset"]) <= utc(row["label_window_end"])):
            raise ValueError("A supplied positive onset must lie inside the future target window.")
        for feature in FEATURES:
            if row[feature] and not math.isfinite(float(row[feature])):
                raise ValueError("Evaluation features must be finite or explicitly missing.")
        usable.append(row)
    return usable, exclusions, mode


def temporal_event_split(rows):
    events = sorted({row["event_id"] for row in rows}, key=lambda event: min(utc(row["issued_at"]) for row in rows if row["event_id"] == event))
    if len(events) < 6:
        raise ValueError("At least six independent events are required for this three-block experiment.")
    train_end = max(2, int(len(events) * .6))
    validation_end = max(train_end + 1, int(len(events) * .8))
    ids = {"train": events[:train_end], "validation": events[train_end:validation_end], "test": events[validation_end:]}
    purged = []
    # Event groups remain intact. Purge earlier events whose 3 h targets overlap
    # the next block's 24 h feature look-back; never peek at target outcomes.
    for previous, following in [("validation", "test"), ("train", "validation")]:
        if not ids[following]:
            raise ValueError("A temporal block became empty after purging.")
        boundary = min(utc(row["issued_at"]) for row in rows if row["event_id"] in ids[following]) - timedelta(hours=24)
        removed = [event for event in ids[previous] if max(utc(row["label_window_end"]) for row in rows if row["event_id"] == event) >= boundary]
        ids[previous] = [event for event in ids[previous] if event not in removed]
        purged.extend(removed)
    blocks = {name: [row for row in rows if row["event_id"] in event_ids] for name, event_ids in ids.items()}
    if any(not block for block in blocks.values()):
        raise ValueError("Insufficient separated events remain for train, validation and test.")
    manifest = {name: {"event_ids": event_ids, "event_count": len(event_ids), "row_count": len(blocks[name]),
                       "row_ids": [row["row_id"] for row in blocks[name]]} for name, event_ids in ids.items()}
    manifest["purged_event_ids"] = purged
    return blocks, manifest


def matrix(rows):
    return np.array([[float(row[feature]) if row[feature] else np.nan for feature in FEATURES] for row in rows], dtype=float)


def metrics(rows, score, threshold, probability_score=True):
    y = np.array([int(row["label"]) for row in rows])
    predicted = (score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    by_event = {}
    by_area = {}
    for row, actual, forecast in zip(rows, y, predicted):
        for group, key in [(by_event, row["event_id"]), (by_area, row["area_id"])]:
            item = group.setdefault(key, {"rows": 0, "missed": 0, "false_alarms": 0})
            item["rows"] += 1
            item["missed"] += int(actual == 1 and forecast == 0)
            item["false_alarms"] += int(actual == 0 and forecast == 1)
    lead = []
    for event in sorted({row["event_id"] for row in rows}):
        paired = [(row, forecast) for row, forecast in zip(rows, predicted) if row["event_id"] == event and row.get("onset") and row["label"] == "1"]
        qualified = [row for row, forecast in paired if forecast]
        if qualified:
            first = min(qualified, key=lambda row: row["issued_at"])
            lead.append({"event_id": event, "minutes": (utc(first["onset"]) - utc(first["issued_at"])).total_seconds() / 60})
    return {"rows": len(rows), "positive_labels": int(y.sum()), "prevalence": round(float(y.mean()), 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
            "recall": round(float(recall_score(y, predicted, zero_division=0)), 4),
            "precision": round(float(precision_score(y, predicted, zero_division=0)), 4),
            "average_precision": round(float(average_precision_score(y, score)), 4) if y.sum() else None,
            "brier_score": round(float(brier_score_loss(y, score)), 4) if probability_score else None,
            "false_positive_rows_per_event": round(int(fp) / max(1, len(by_event)), 2),
            "by_event": by_event, "by_area": by_area, "lead_times": lead}


def evaluate(settings, csv_path: Path | None = None):
    source = csv_path or ROOT / "data" / "fixtures" / "synthetic_evaluation.csv"
    if not source.exists() and csv_path is None:
        create_synthetic_experiment(source)
    rows, exclusions, mode = eligible_rows(source)
    blocks, split = temporal_event_split(rows)
    training, validation, test = blocks["train"], blocks["validation"], blocks["test"]
    y_train = np.array([int(row["label"]) for row in training])
    if len(set(y_train)) < 2:
        raise ValueError("Training requires both credible positive and negative labels; keep the fallback otherwise.")
    model = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)),
                      ("scale", StandardScaler()),
                      ("classifier", LogisticRegression(class_weight="balanced", random_state=SEED, max_iter=1000))])
    model.fit(matrix(training), y_train)
    validation_scores = model.predict_proba(matrix(validation))[:, 1]
    y_validation = np.array([int(row["label"]) for row in validation])
    threshold = max([.2, .3, .4, .5, .6, .7], key=lambda value: (fbeta_score(y_validation, validation_scores >= value, beta=2, zero_division=0), value))
    # The threshold is frozen before the first final-test prediction.
    test_scores = model.predict_proba(matrix(test))[:, 1]
    candidate = metrics(test, test_scores, threshold)
    rule_score = np.array([float(row["rainfall_3h_mm"]) / 75 if row["rainfall_3h_mm"] else 0 for row in test])
    rule_score = np.clip(rule_score, 0, 1)
    baseline = metrics(test, rule_score, 1, probability_score=False)
    prevalence = metrics(test, np.repeat(float(y_train.mean()), len(test)), .5)
    result = {"status": "software_experiment_complete" if mode == "synthetic" else "historical_experiment_requires_evidence_review",
              "mode": mode, "historical_accuracy_established": False, "candidate_promoted": False,
              "reason": "Synthetic labels establish software behavior only; real-world forecasting accuracy is not established." if mode == "synthetic" else "Data provenance and the held-out comparison require human evidence review before a forecast can be promoted.",
              "rule_version": RULE_VERSION, "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "seed": SEED, "features": FEATURES, "independent_events": len({row["event_id"] for row in rows}), "usable_rows": len(rows),
              "excluded_rows": exclusions, "split": split, "candidate": {"name": "logistic_regression", "threshold": threshold, "test": candidate},
              "rainfall_baseline": baseline, "prevalence_baseline": prevalence,
              "calibration_supported": False, "metric_intervals": None,
              "uncertainty_note": "The held-out event count is too small for stable calibration or event-bootstrap intervals. Row independence is not assumed.",
              "split_fingerprint": fingerprint(split), "preprocessing_fitted_on": "train_only", "threshold_selected_on": "validation_only"}
    folder = settings.runtime / "model_candidates"
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "threshold": threshold, "data_mode": mode, "promoted": False}, folder / "logistic_regression.joblib")
    (settings.runtime / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
