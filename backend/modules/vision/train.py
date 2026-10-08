#!/usr/bin/env python3
"""
SpaceLoop Room Condition Vision Model Trainer
=============================================
Trains a scikit-learn classifier on visual condition-delta feature vectors extracted
from paired BEFORE (check-in) and AFTER (check-out) room condition images.

Supported Target Classes:
    - CLEAN (0)
    - MINOR_CHANGE (1)
    - SIGNIFICANT_CHANGE (2)
    - DAMAGE (3)

Outputs:
    - Serialized pipeline artifact: backend/modules/vision/artifacts/room_condition_model_v1.joblib
    - Metrics: Classification report, confusion matrix, train/test accuracy, top feature importances.
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Ensure module imports resolve whether run directly or as package
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.modules.vision.features import extract_pair_features, FEATURE_NAMES
from backend.modules.vision.dataset import (
    SUPPORTED_LABELS,
    LABEL_TO_ID,
    ID_TO_LABEL,
    PairSample,
    load_paired_dataset,
    get_dataset_class_counts,
)


DEFAULT_DATASET_DIR = os.path.join(CURRENT_DIR, "dataset")
DEFAULT_ARTIFACT_DIR = os.path.join(CURRENT_DIR, "artifacts")
DEFAULT_MODEL_FILENAME = "room_condition_model_v1.joblib"


def extract_dataset_features(
    samples: List[PairSample],
    verbose: bool = True
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Extracts 107-dimensional feature vectors from all image pairs.
    Returns (X, y, valid_pair_ids).
    """
    X_list: List[np.ndarray] = []
    y_list: List[int] = []
    valid_ids: List[str] = []

    total = len(samples)
    for idx, sample in enumerate(samples, 1):
        if verbose and (idx % 10 == 0 or idx == total or idx == 1):
            print(f"  [{idx}/{total}] Extracting features for pair '{sample.pair_id}' ({sample.label})...")

        try:
            _, vec = extract_pair_features(sample.before_path, sample.after_path)
            X_list.append(vec)
            y_list.append(sample.label_id)
            valid_ids.append(sample.pair_id)
        except Exception as err:
            print(f"  [WARNING] Failed to extract features for pair '{sample.pair_id}': {err}")

    if not X_list:
        raise ValueError("No feature vectors could be extracted from the dataset samples.")

    X = np.vstack(X_list).astype(np.float32)
    y = np.array(y_list, dtype=np.int64)
    return X, y, valid_ids


def train_room_condition_model(
    dataset_dir: str = DEFAULT_DATASET_DIR,
    artifact_dir: str = DEFAULT_ARTIFACT_DIR,
    model_filename: str = DEFAULT_MODEL_FILENAME,
    test_size: float = 0.25,
    random_state: int = 42,
    n_estimators: int = 100,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Runs the complete training and evaluation pipeline on paired images.
    Returns training results dictionary.
    """
    if verbose:
        print("=" * 70)
        print("SPACELOOP COMPUTER VISION CONDITION-DELTA MODEL TRAINING")
        print("=" * 70)
        print(f"Dataset Directory : {dataset_dir}")
        print(f"Artifact Directory: {artifact_dir}")
        print(f"Target Artifact   : {os.path.join(artifact_dir, model_filename)}")
        print(f"Supported Classes : {', '.join(SUPPORTED_LABELS)}")
        print("-" * 70)

    # 1. Load paired dataset
    samples = load_paired_dataset(dataset_dir)
    if not samples:
        print("\n[STATUS: TRAINING DATA REQUIRED]")
        print(f"No valid image pairs found in '{dataset_dir}'.")
        print("\nExpected directory layout:")
        for lbl in SUPPORTED_LABELS:
            print(f"  {dataset_dir}/{lbl}/")
            print(f"      sample_001_before.jpg")
            print(f"      sample_001_after.jpg")
        print("\nPlease populate the dataset directories with real before/after photo pairs.")
        print("Run `python train.py --help` for full dataset layout and options.")
        return {
            "status": "DATA_REQUIRED",
            "message": "No paired images found in dataset directory.",
            "num_samples": 0,
            "trained": False,
        }

    counts = get_dataset_class_counts(samples)
    if verbose:
        print(f"Loaded {len(samples)} image pairs across classes:")
        for lbl, count in counts.items():
            print(f"  • {lbl:<20}: {count} pairs")
        print("-" * 70)

    # Validate that we have sufficient samples to train
    present_classes = [lbl for lbl, c in counts.items() if c > 0]
    if len(present_classes) < 2:
        print("\n[STATUS: INSUFFICIENT CLASS DIVERSITY]")
        print(f"Found pairs for only {len(present_classes)} class ({present_classes}).")
        print("Training requires samples across at least 2 distinct condition classes.")
        return {
            "status": "INSUFFICIENT_CLASSES",
            "num_samples": len(samples),
            "trained": False,
        }

    # 2. Extract feature vectors
    if verbose:
        print("Extracting 107-dimensional condition-delta visual features...")
    X, y, pair_ids = extract_dataset_features(samples, verbose=verbose)
    if verbose:
        print(f"Feature matrix shape: {X.shape} (Features per pair: {len(FEATURE_NAMES)})")
        print("-" * 70)

    # 3. Train / Test Split
    # Check if all present classes have at least 2 samples for stratification
    can_stratify = all(counts[lbl] >= 2 for lbl in present_classes) and len(X) >= (len(present_classes) * 2)
    stratify_target = y if can_stratify else None

    # Handle very small test setups gracefully
    eff_test_size = test_size if len(X) >= 8 else 0.2
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=eff_test_size, random_state=random_state, stratify=stratify_target
    )

    if verbose:
        print(f"Train set size: {len(X_train)} pairs")
        print(f"Test set size : {len(X_test)} pairs")
        print("-" * 70)

    # 4. Train Pipeline (StandardScaler + Balanced Random Forest)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=12,
            min_samples_split=2,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )),
    ])

    if verbose:
        print("Training Random Forest Classifier on visual condition-delta vectors...")
    pipeline.fit(X_train, y_train)

    # 5. Evaluate on Train and Test Sets (Actual metrics only)
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

    train_acc = float(accuracy_score(y_train, y_train_pred))
    test_acc = float(accuracy_score(y_test, y_test_pred))

    # Identify unique classes present in test set for report
    unique_test_labels = sorted(list(set(y_test) | set(y_test_pred)))
    target_names = [ID_TO_LABEL[idx] for idx in unique_test_labels]

    report_dict = classification_report(
        y_test, y_test_pred, labels=unique_test_labels, target_names=target_names, output_dict=True, zero_division=0
    )
    report_text = classification_report(
        y_test, y_test_pred, labels=unique_test_labels, target_names=target_names, zero_division=0
    )
    cm = confusion_matrix(y_test, y_test_pred, labels=unique_test_labels)

    # Extract feature importances
    rf_model: RandomForestClassifier = pipeline.named_steps["classifier"]
    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    top_features = [(FEATURE_NAMES[i], float(importances[i])) for i in sorted_idx[:10]]

    if verbose:
        print("=" * 70)
        print("TRAINING METRICS (ACTUAL EVALUATION ON TEST SPLIT)")
        print("=" * 70)
        print(f"Training Accuracy : {train_acc * 100:.2f}% ({np.sum(y_train == y_train_pred)}/{len(y_train)})")
        print(f"Test Accuracy     : {test_acc * 100:.2f}% ({np.sum(y_test == y_test_pred)}/{len(y_test)})")
        print("\nClassification Report (Test Split):")
        print(report_text)
        print("Confusion Matrix:")
        print(cm)
        print("\nTop 10 Most Discriminative Visual Features:")
        for rank, (name, imp) in enumerate(top_features, 1):
            print(f"  {rank:>2}. {name:<32} (Importance: {imp * 100:.2f}%)")
        print("-" * 70)

    # 6. Save Artifact
    os.makedirs(artifact_dir, exist_ok=True)
    saved_model_path = os.path.join(artifact_dir, model_filename)

    artifact_bundle = {
        "model": pipeline,
        "feature_names": FEATURE_NAMES,
        "labels": SUPPORTED_LABELS,
        "label_to_id": LABEL_TO_ID,
        "id_to_label": ID_TO_LABEL,
        "metrics": {
            "train_accuracy": train_acc,
            "test_accuracy": test_acc,
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist(),
            "num_total_samples": len(samples),
            "num_train_samples": len(X_train),
            "num_test_samples": len(X_test),
            "class_distribution": counts,
        },
        "top_features": top_features,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }

    joblib.dump(artifact_bundle, saved_model_path)
    if verbose:
        print(f"Model artifact saved to: {saved_model_path}")
        print("=" * 70)

    return {
        "status": "SUCCESS",
        "trained": True,
        "artifact_path": saved_model_path,
        "num_samples": len(samples),
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "classification_report": report_dict,
        "top_features": top_features,
    }


def _generate_synthetic_sample_data(target_dir: str, pairs_per_class: int = 5) -> None:
    """
    Utility generator creating synthetic reference image pairs for pipeline verification.
    Generates deterministic PIL images illustrating clean vs changed vs damaged states.
    """
    from PIL import Image, ImageDraw

    os.makedirs(target_dir, exist_ok=True)
    for lbl in SUPPORTED_LABELS:
        os.makedirs(os.path.join(target_dir, lbl), exist_ok=True)

    print(f"Generating {pairs_per_class} synthetic sample pairs per class in '{target_dir}'...")

    for lbl in SUPPORTED_LABELS:
        class_folder = os.path.join(target_dir, lbl)
        for i in range(1, pairs_per_class + 1):
            pair_prefix = f"sample_{i:03d}"
            b_path = os.path.join(class_folder, f"{pair_prefix}_before.jpg")
            a_path = os.path.join(class_folder, f"{pair_prefix}_after.jpg")

            # Base room image (gray floor, beige wall, desk)
            base = Image.new("RGB", (256, 256), color=(220, 215, 205))
            draw_b = ImageDraw.Draw(base)
            draw_b.rectangle([(0, 150), (256, 256)], fill=(120, 115, 110))  # floor
            draw_b.rectangle([(50, 120), (200, 170)], fill=(90, 60, 40))    # desk
            draw_b.rectangle([(80, 100), (120, 120)], fill=(40, 40, 50))    # laptop

            # Create 'after' variant based on label
            after = base.copy()
            draw_a = ImageDraw.Draw(after)

            if lbl == "CLEAN":
                # Identical with microscopic sensor noise
                arr = np.asarray(after, dtype=np.int16)
                noise = np.random.RandomState(i).randint(-2, 3, arr.shape)
                after = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

            elif lbl == "MINOR_CHANGE":
                # Small shifted paper or water bottle on desk
                draw_a.ellipse([(140, 105), (155, 120)], fill=(30, 120, 200))

            elif lbl == "SIGNIFICANT_CHANGE":
                # Lights off (dimmed image) + scattered waste on floor
                arr = np.asarray(after, dtype=np.float32) * 0.45  # lights off
                after = Image.fromarray(arr.astype(np.uint8))
                draw_a = ImageDraw.Draw(after)
                draw_a.rectangle([(60, 190), (95, 215)], fill=(200, 50, 50))  # trash bag
                draw_a.ellipse([(170, 180), (190, 195)], fill=(240, 240, 240)) # cups

            elif lbl == "DAMAGE":
                # Large stain on wall / desk fracture
                draw_a.polygon([(100, 40), (135, 70), (120, 110), (85, 80)], fill=(40, 25, 20)) # wall stain
                draw_a.line([(50, 145), (120, 145)], fill=(20, 20, 20), width=4) # broken desk

            base.save(b_path, "JPEG", quality=90)
            after.save(a_path, "JPEG", quality=90)

    print(f"Synthetic sample data generated: {pairs_per_class * len(SUPPORTED_LABELS)} total pairs.")


def main():
    parser = argparse.ArgumentParser(description="SpaceLoop Condition-Delta Vision Model Trainer")
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR, help="Path to paired dataset directory")
    parser.add_argument("--artifact-dir", default=DEFAULT_ARTIFACT_DIR, help="Path to save trained artifacts")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_FILENAME, help="Artifact filename")
    parser.add_argument("--test-size", type=float, default=0.25, help="Test set fraction")
    parser.add_argument("--n-estimators", type=int, default=100, help="Number of trees in Random Forest")
    parser.add_argument("--generate-sample-data", action="store_true", help="Generate synthetic paired samples for pipeline test run")
    parser.add_argument("--sample-count", type=int, default=5, help="Samples per class when generating test data")
    args = parser.parse_args()

    if args.generate_sample_data:
        _generate_synthetic_sample_data(args.dataset_dir, pairs_per_class=args.sample_count)

    res = train_room_condition_model(
        dataset_dir=args.dataset_dir,
        artifact_dir=args.artifact_dir,
        model_filename=args.model_name,
        test_size=args.test_size,
        n_estimators=args.n_estimators,
        verbose=True,
    )

    if not res.get("trained"):
        sys.exit(1)


if __name__ == "__main__":
    main()
