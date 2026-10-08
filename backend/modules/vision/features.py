"""
SpaceLoop Vision Feature Extractor
==================================
Calculates meaningful computer-vision condition-delta features from paired
BEFORE (baseline/check-in) and AFTER (inspection/check-out) room images.

Dependencies:
    - Pillow (PIL)
    - NumPy

Features Extracted:
    1. Pixel-level differences: Mean absolute error (L1), MSE (L2), PSNR, changed pixel ratios.
    2. Luminance & Electrical state: Mean brightness delta, variance delta, high-luminance light ratios.
    3. Structural Similarity (SSIM-style): Global SSIM, luminance/contrast/structure components,
       patch-level min/mean SSIM (localized anomaly detection), intensity correlation.
    4. Color histogram differences: Histogram intersection, correlation, Chi-squared, Euclidean delta.
    5. Edge & Contour differences: Sobel/gradient magnitude deltas, edge displacement ratios.
    6. Spatial Grid Differences: 8x8 downsampled regional difference map for spatial locality.
"""

from typing import Union, Tuple, Dict, List
import os
import io
import math
import numpy as np
from PIL import Image

STANDARD_SIZE: Tuple[int, int] = (256, 256)
GRID_DIMS: Tuple[int, int] = (8, 8)


def _build_feature_names() -> List[str]:
    """Generates the fixed canonical list of feature names."""
    names = [
        # 1. Pixel-level difference features
        "mean_abs_diff_all",
        "mean_abs_diff_r",
        "mean_abs_diff_g",
        "mean_abs_diff_b",
        "std_abs_diff",
        "max_abs_diff",
        "mse",
        "psnr",
        "fraction_pixels_changed_5pct",
        "fraction_pixels_changed_15pct",
        "fraction_pixels_changed_30pct",

        # 2. Luminance & electrical indicators
        "lum_mean_before",
        "lum_mean_after",
        "delta_luminance",
        "abs_delta_luminance",
        "lum_var_before",
        "lum_var_after",
        "delta_lum_variance",
        "high_lum_ratio_before",
        "high_lum_ratio_after",
        "delta_high_lum_ratio",
        "low_lum_ratio_before",
        "low_lum_ratio_after",
        "delta_low_lum_ratio",

        # 3. Structural / SSIM-style features
        "global_ssim",
        "ssim_luminance_comp",
        "ssim_contrast_comp",
        "ssim_structure_comp",
        "intensity_correlation",
        "patch_ssim_mean",
        "patch_ssim_min",
        "patch_ssim_std",

        # 4. Color histogram features
        "color_hist_intersection",
        "color_hist_correlation",
        "color_hist_chi_square",
        "color_hist_euclidean",
        "delta_color_entropy",

        # 5. Edge / gradient change features
        "mean_edge_before",
        "mean_edge_after",
        "delta_mean_edge",
        "mean_abs_edge_diff",
        "std_edge_diff",
        "fraction_edges_altered",
    ]

    # 6. 8x8 Spatial grid difference features (64 regional values)
    for r in range(GRID_DIMS[0]):
        for c in range(GRID_DIMS[1]):
            names.append(f"grid_diff_{r}_{c}")

    return names


FEATURE_NAMES: List[str] = _build_feature_names()
NUM_FEATURES: int = len(FEATURE_NAMES)


def load_image_as_rgb(image_input: Union[str, Image.Image, np.ndarray, bytes, io.BytesIO]) -> Image.Image:
    """
    Standardizes any image input (filepath, PIL Image, NumPy array, or bytes)
    into a PIL RGB Image.
    """
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")
    elif isinstance(image_input, (str, os.PathLike)):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image file does not exist: {image_input}")
        with Image.open(image_input) as img:
            return img.convert("RGB")
    elif isinstance(image_input, (bytes, bytearray)):
        with Image.open(io.BytesIO(image_input)) as img:
            return img.convert("RGB")
    elif isinstance(image_input, io.BytesIO):
        image_input.seek(0)
        with Image.open(image_input) as img:
            return img.convert("RGB")
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            return Image.fromarray(image_input).convert("RGB")
        elif image_input.ndim == 3:
            if image_input.shape[2] == 4:
                return Image.fromarray(image_input).convert("RGB")
            return Image.fromarray(image_input.astype(np.uint8), mode="RGB")
        raise ValueError(f"Unsupported NumPy array shape for image: {image_input.shape}")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")


def _compute_ssim(
    lum1: np.ndarray,
    lum2: np.ndarray,
    c1: float = (0.01) ** 2,
    c2: float = (0.03) ** 2,
) -> Tuple[float, float, float, float]:
    """
    Computes global structural similarity index and its constituent terms:
    Returns (ssim, l_comp, c_comp, s_comp).
    """
    mu1 = float(np.mean(lum1))
    mu2 = float(np.mean(lum2))
    var1 = float(np.var(lum1))
    var2 = float(np.var(lum2))
    cov12 = float(np.mean((lum1 - mu1) * (lum2 - mu2)))

    std1 = math.sqrt(max(var1, 1e-12))
    std2 = math.sqrt(max(var2, 1e-12))

    l_comp = (2 * mu1 * mu2 + c1) / (mu1**2 + mu2**2 + c1)
    c_comp = (2 * std1 * std2 + c2) / (var1 + var2 + c2)
    s_comp = (cov12 + (c2 / 2)) / (std1 * std2 + (c2 / 2))

    ssim = float(np.clip(l_comp * c_comp * s_comp, -1.0, 1.0))
    return ssim, float(l_comp), float(c_comp), float(s_comp)


def _compute_patch_ssim(lum1: np.ndarray, lum2: np.ndarray, patches: int = 4) -> Tuple[float, float, float]:
    """
    Computes SSIM over a grid of local spatial patches to detect localized damage or stains.
    Returns (patch_mean, patch_min, patch_std).
    """
    h, w = lum1.shape
    ph, pw = h // patches, w // patches
    scores: List[float] = []

    for r in range(patches):
        for c in range(patches):
            p1 = lum1[r * ph : (r + 1) * ph, c * pw : (c + 1) * pw]
            p2 = lum2[r * ph : (r + 1) * ph, c * pw : (c + 1) * pw]
            score, _, _, _ = _compute_ssim(p1, p2)
            scores.append(score)

    arr = np.array(scores, dtype=np.float32)
    return float(np.mean(arr)), float(np.min(arr)), float(np.std(arr))


def _compute_edges(lum: np.ndarray) -> np.ndarray:
    """Computes gradient magnitude edge map using central differences."""
    gx = np.zeros_like(lum)
    gy = np.zeros_like(lum)
    gx[:, 1:-1] = (lum[:, 2:] - lum[:, :-2]) * 0.5
    gy[1:-1, :] = (lum[2:, :] - lum[:-2, :]) * 0.5
    return np.sqrt(gx**2 + gy**2)


def _compute_color_histogram_stats(arr1: np.ndarray, arr2: np.ndarray, bins: int = 16) -> Dict[str, float]:
    """Computes comparative distance metrics between normalized RGB histograms."""
    hists1 = []
    hists2 = []

    for ch in range(3):
        h1, _ = np.histogram(arr1[:, :, ch], bins=bins, range=(0.0, 1.0), density=True)
        h2, _ = np.histogram(arr2[:, :, ch], bins=bins, range=(0.0, 1.0), density=True)
        h1 = h1 / (np.sum(h1) + 1e-12)
        h2 = h2 / (np.sum(h2) + 1e-12)
        hists1.append(h1)
        hists2.append(h2)

    vec1 = np.concatenate(hists1)
    vec2 = np.concatenate(hists2)

    # 1. Intersection (1.0 = identical)
    intersection = float(np.sum(np.minimum(vec1, vec2)) / 3.0)

    # 2. Pearson correlation
    v1_centered = vec1 - np.mean(vec1)
    v2_centered = vec2 - np.mean(vec2)
    denom = np.sqrt(np.sum(v1_centered**2) * np.sum(v2_centered**2))
    correlation = float(np.sum(v1_centered * v2_centered) / (denom + 1e-12)) if denom > 0 else 1.0

    # 3. Chi-squared distance
    chi_sq = float(np.sum(((vec1 - vec2) ** 2) / (vec1 + vec2 + 1e-12)))

    # 4. Euclidean distance
    euclidean = float(np.linalg.norm(vec1 - vec2))

    # 5. Shannon entropy difference
    p1 = vec1[vec1 > 0]
    p2 = vec2[vec2 > 0]
    ent1 = -float(np.sum(p1 * np.log2(p1)))
    ent2 = -float(np.sum(p2 * np.log2(p2)))
    delta_entropy = float(abs(ent2 - ent1))

    return {
        "color_hist_intersection": float(np.clip(intersection, 0.0, 1.0)),
        "color_hist_correlation": float(np.clip(correlation, -1.0, 1.0)),
        "color_hist_chi_square": float(max(0.0, chi_sq)),
        "color_hist_euclidean": float(max(0.0, euclidean)),
        "delta_color_entropy": float(max(0.0, delta_entropy)),
    }


def extract_pair_features(
    before_input: Union[str, Image.Image, np.ndarray, bytes, io.BytesIO],
    after_input: Union[str, Image.Image, np.ndarray, bytes, io.BytesIO],
    standard_size: Tuple[int, int] = STANDARD_SIZE,
    grid_dims: Tuple[int, int] = GRID_DIMS,
) -> Tuple[Dict[str, float], np.ndarray]:
    """
    Extracts all condition-delta features between a before image and an after image.

    Args:
        before_input: Path, PIL Image, numpy array, or bytes of the baseline check-in image.
        after_input: Path, PIL Image, numpy array, or bytes of the exit check-out image.
        standard_size: Standard resolution for image comparison (default 256x256).
        grid_dims: Grid dimensions for regional spatial difference map (default 8x8).

    Returns:
        (features_dict, feature_vector):
            - features_dict: mapping of feature name -> float value
            - feature_vector: 1D numpy array of shape (NUM_FEATURES,), dtype float32
    """
    # 1. Load and resize both images to standard dimensions
    img_before = load_image_as_rgb(before_input).resize(standard_size, Image.Resampling.BILINEAR)
    img_after = load_image_as_rgb(after_input).resize(standard_size, Image.Resampling.BILINEAR)

    # 2. Convert to normalized float arrays [0.0, 1.0]
    arr_before = np.asarray(img_before, dtype=np.float32) / 255.0
    arr_after = np.asarray(img_after, dtype=np.float32) / 255.0

    # 3. Compute luminance (standard Rec. 601 grayscale weights)
    lum_before = (0.299 * arr_before[:, :, 0] + 0.587 * arr_before[:, :, 1] + 0.114 * arr_before[:, :, 2])
    lum_after = (0.299 * arr_after[:, :, 0] + 0.587 * arr_after[:, :, 1] + 0.114 * arr_after[:, :, 2])

    features: Dict[str, float] = {}

    # --- Group 1: Pixel-level difference features ---
    diff_rgb = np.abs(arr_before - arr_after)
    diff_lum = np.abs(lum_before - lum_after)

    features["mean_abs_diff_all"] = float(np.mean(diff_rgb))
    features["mean_abs_diff_r"] = float(np.mean(diff_rgb[:, :, 0]))
    features["mean_abs_diff_g"] = float(np.mean(diff_rgb[:, :, 1]))
    features["mean_abs_diff_b"] = float(np.mean(diff_rgb[:, :, 2]))
    features["std_abs_diff"] = float(np.std(diff_rgb))
    features["max_abs_diff"] = float(np.max(diff_rgb))

    mse_val = float(np.mean((arr_before - arr_after) ** 2))
    features["mse"] = mse_val
    features["psnr"] = float(10.0 * math.log10(1.0 / (mse_val + 1e-10))) if mse_val > 0 else 60.0

    features["fraction_pixels_changed_5pct"] = float(np.mean(diff_lum > 0.05))
    features["fraction_pixels_changed_15pct"] = float(np.mean(diff_lum > 0.15))
    features["fraction_pixels_changed_30pct"] = float(np.mean(diff_lum > 0.30))

    # --- Group 2: Luminance & electrical indicators ---
    mean_lum_b = float(np.mean(lum_before))
    mean_lum_a = float(np.mean(lum_after))
    features["lum_mean_before"] = mean_lum_b
    features["lum_mean_after"] = mean_lum_a
    features["delta_luminance"] = mean_lum_a - mean_lum_b
    features["abs_delta_luminance"] = abs(mean_lum_a - mean_lum_b)

    var_lum_b = float(np.var(lum_before))
    var_lum_a = float(np.var(lum_after))
    features["lum_var_before"] = var_lum_b
    features["lum_var_after"] = var_lum_a
    features["delta_lum_variance"] = abs(var_lum_a - var_lum_b)

    high_b = float(np.mean(lum_before > 0.85))
    high_a = float(np.mean(lum_after > 0.85))
    features["high_lum_ratio_before"] = high_b
    features["high_lum_ratio_after"] = high_a
    features["delta_high_lum_ratio"] = high_a - high_b

    low_b = float(np.mean(lum_before < 0.15))
    low_a = float(np.mean(lum_after < 0.15))
    features["low_lum_ratio_before"] = low_b
    features["low_lum_ratio_after"] = low_a
    features["delta_low_lum_ratio"] = low_a - low_b

    # --- Group 3: Structural / SSIM-style features ---
    ssim_val, l_comp, c_comp, s_comp = _compute_ssim(lum_before, lum_after)
    features["global_ssim"] = ssim_val
    features["ssim_luminance_comp"] = l_comp
    features["ssim_contrast_comp"] = c_comp
    features["ssim_structure_comp"] = s_comp

    v_b = lum_before.ravel() - np.mean(lum_before)
    v_a = lum_after.ravel() - np.mean(lum_after)
    denom = np.sqrt(np.sum(v_b**2) * np.sum(v_a**2))
    features["intensity_correlation"] = float(np.sum(v_b * v_a) / (denom + 1e-12)) if denom > 0 else 1.0

    p_mean, p_min, p_std = _compute_patch_ssim(lum_before, lum_after, patches=4)
    features["patch_ssim_mean"] = p_mean
    features["patch_ssim_min"] = p_min
    features["patch_ssim_std"] = p_std

    # --- Group 4: Color histogram features ---
    hist_stats = _compute_color_histogram_stats(arr_before, arr_after)
    features.update(hist_stats)

    # --- Group 5: Edge & Contour differences ---
    edge_before = _compute_edges(lum_before)
    edge_after = _compute_edges(lum_after)
    edge_diff = np.abs(edge_before - edge_after)

    mean_eb = float(np.mean(edge_before))
    mean_ea = float(np.mean(edge_after))
    features["mean_edge_before"] = mean_eb
    features["mean_edge_after"] = mean_ea
    features["delta_mean_edge"] = abs(mean_ea - mean_eb)
    features["mean_abs_edge_diff"] = float(np.mean(edge_diff))
    features["std_edge_diff"] = float(np.std(edge_diff))
    features["fraction_edges_altered"] = float(np.mean(edge_diff > 0.15))

    # --- Group 6: Spatial Grid Differences ---
    # Downsample difference map to grid_dims
    grid_h = standard_size[0] // grid_dims[0]
    grid_w = standard_size[1] // grid_dims[1]
    for r in range(grid_dims[0]):
        for c in range(grid_dims[1]):
            block = diff_lum[r * grid_h : (r + 1) * grid_h, c * grid_w : (c + 1) * grid_w]
            features[f"grid_diff_{r}_{c}"] = float(np.mean(block))

    # Build canonical 1D float32 vector aligned with FEATURE_NAMES
    vector = np.array([features[name] for name in FEATURE_NAMES], dtype=np.float32)

    return features, vector
