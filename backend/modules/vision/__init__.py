"""
SpaceLoop Vision Inspection Module
==================================
Provides lightweight computer-vision feature extraction, paired-image dataset management,
and model training for Before vs. After room condition inspection.
"""

try:
    from .features import extract_pair_features, FEATURE_NAMES
    from .dataset import (
        SUPPORTED_LABELS,
        LABEL_TO_ID,
        ID_TO_LABEL,
        PairSample,
        load_paired_dataset,
    )
except ImportError:
    FEATURE_NAMES = []
    SUPPORTED_LABELS = []
    LABEL_TO_ID = {}
    ID_TO_LABEL = {}
    PairSample = None
    extract_pair_features = None
    load_paired_dataset = None

__all__ = [
    "extract_pair_features",
    "FEATURE_NAMES",
    "SUPPORTED_LABELS",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
    "PairSample",
    "load_paired_dataset",
]
