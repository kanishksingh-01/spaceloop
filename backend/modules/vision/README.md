# SpaceLoop Computer Vision Room Inspection Module

This module provides a lightweight, dedicated computer-vision feature extraction and training pipeline for evaluating room condition changes between **Before (Check-In / Baseline)** and **After (Check-Out / Inspection)** photo pairs.

It is built strictly using existing project dependencies:
- **Pillow** (`PIL`) for image processing and edge analysis
- **NumPy** for vector and matrix operations
- **scikit-learn** for pipeline scaling, classification, and evaluation
- **joblib** for model serialization

No heavyweight frameworks (PyTorch or TensorFlow) are required.

---

## 1. Directory Structure

```text
backend/modules/vision/
├── __init__.py           # Package exports (extract_pair_features, load_paired_dataset, etc.)
├── features.py           # 107-dimensional condition-delta visual feature extractor
├── dataset.py            # Paired BEFORE/AFTER dataset loader and validation
├── train.py              # scikit-learn training, evaluation, and artifact export script
├── README.md             # Pipeline documentation
├── dataset/              # Training image dataset directory
│   ├── CLEAN/            # Pairs where room condition is unchanged
│   ├── MINOR_CHANGE/     # Pairs with negligible shifts (chair moved, water bottle)
│   ├── SIGNIFICANT_CHANGE/ # Pairs with lights left on, unarranged furniture, trash
│   └── DAMAGE/           # Pairs with structural scratches, wall stains, broken fixtures
└── artifacts/            # Trained model destination
    └── room_condition_model_v1.joblib (generated upon training)
```

---

## 2. Supported Condition Labels

The pipeline supports four target classes:

| Class Label | ID | Description |
| :--- | :---: | :--- |
| `CLEAN` | `0` | Identical condition to check-in; furniture unchanged, appliances off, zero waste. |
| `MINOR_CHANGE` | `1` | Minor permissible shift (e.g., chair adjusted slightly, personal jacket on chair). |
| `SIGNIFICANT_CHANGE` | `2` | Lights/fans left running, visible surface trash, unarranged furniture. |
| `DAMAGE` | `3` | Physical damage, wall/floor stains, broken fixtures, property defects. |

---

## 3. How Before / After Image Pairs Are Represented

The dataset loader (`dataset.py`) supports three paired formats within each class folder (`dataset/{LABEL}/`):

### Option A: Suffix-based filename matching (Recommended)
Place both images directly inside the class folder with matching pair IDs and suffixes:
```text
dataset/CLEAN/
    pair_001_before.jpg
    pair_001_after.jpg
    pair_002_before.png
    pair_002_after.png
```
Supported suffixes:
- `_before` / `_after`
- `-before` / `-after`
- `_entry` / `_exit`
- `_pre` / `_post`

### Option B: Subdirectory per pair
Create a subdirectory for each pair inside the class folder:
```text
dataset/DAMAGE/
    broken_table_01/
        before.jpg
        after.jpg
```

### Option C: Manifest File
Provide a `manifest.csv` or `manifest.json` pointing to before/after paths:
```csv
pair_id,before_path,after_path,label
sample_01,/path/to/b1.jpg,/path/to/a1.jpg,CLEAN
```

Supported image extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`.

---

## 4. Visual Feature Extraction (107 Dimensions)

The feature extractor (`features.py`) standardizes both images to 256x256 RGB and computes 107 deterministic delta features:

1. **Pixel-Level Differences (11 features)**:
   - Mean Absolute Error (overall L1, Red channel L1, Green channel L1, Blue channel L1)
   - Standard deviation & maximum absolute pixel delta
   - Mean Squared Error (MSE, L2)
   - Peak Signal-to-Noise Ratio (PSNR)
   - Fraction of pixels changed beyond 5%, 15%, and 30% intensity thresholds

2. **Luminance & Appliance Indicators (13 features)**:
   - Mean luminance before & after
   - Signed and absolute luminance delta (detects lights left on or turned off)
   - Luminance variance before & after
   - High-luminance pixel ratios (>85% brightness) before & after (detects glowing bulbs/fixtures)
   - Low-luminance pixel ratios (<15% brightness) before & after

3. **Structural Similarity / SSIM-Style (8 features)**:
   - Global SSIM index
   - SSIM components: Luminance comparison, Contrast comparison, Structure comparison
   - Intensity Pearson correlation
   - Patch-level SSIM (mean, minimum, standard deviation across 16x16 local patches to detect localized anomalies)

4. **Color Histogram Differences (5 features)**:
   - Normalized 3D/flattened RGB color histogram intersection
   - Histogram correlation
   - Chi-squared histogram distance
   - Euclidean color histogram distance
   - Color Shannon entropy delta

5. **Edge & Gradient Alterations (6 features)**:
   - Mean Sobel gradient magnitude before & after
   - Signed edge magnitude difference
   - Mean absolute edge difference
   - Fraction of edge pixels altered

6. **8x8 Spatial Difference Grid (64 features)**:
   - Downsampled 8x8 spatial grid of absolute differences (`grid_diff_0_0` through `grid_diff_7_7`), preserving spatial location of room alterations.

---

## 5. How to Run Training

### Standard Training Command
Activate the virtual environment and execute `train.py`:

```bash
# Using project virtualenv:
./venv/bin/python backend/modules/vision/train.py

# Or with activated venv:
python backend/modules/vision/train.py
```

### CLI Arguments
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--dataset-dir` | `backend/modules/vision/dataset` | Path to labeled image pairs |
| `--artifact-dir` | `backend/modules/vision/artifacts` | Path to save trained artifact |
| `--model-name` | `room_condition_model_v1.joblib` | Target joblib artifact filename |
| `--test-size` | `0.25` | Fraction of data reserved for test evaluation |
| `--n-estimators` | `100` | Number of trees in RandomForestClassifier |
| `--generate-sample-data` | `False` | Generates synthetic sample pairs to test pipeline |
| `--sample-count` | `5` | Number of synthetic pairs per class if generating |

---

## 6. Model Artifact Output

When training completes, the model is serialized via `joblib` to:
```text
backend/modules/vision/artifacts/room_condition_model_v1.joblib
```

The artifact is a dictionary containing:
- `"model"`: The trained scikit-learn `Pipeline([('scaler', StandardScaler()), ('classifier', RandomForestClassifier())])`
- `"feature_names"`: Canonical list of 107 feature names
- `"labels"`: Supported class labels list
- `"label_to_id"` & `"id_to_label"`: Label mapping dictionaries
- `"metrics"`: Actual evaluated training and test metrics
- `"top_features"`: Top-10 most discriminative features by Gini importance
- `"trained_at"`: UTC ISO-8601 timestamp
- `"version"`: Pipeline schema version (`"1.0.0"`)

---

## 7. Generated Metrics

The training script computes and reports **only actual, non-fabricated metrics**:
- **Training Accuracy**: Accuracy score on the training split
- **Test Accuracy**: Accuracy score on the held-out test split
- **Classification Report**: Per-class Precision, Recall, and F1-score
- **Confusion Matrix**: Full breakdown of true vs predicted classes
- **Top 10 Feature Importances**: Percentage contribution of the most decisive visual features
