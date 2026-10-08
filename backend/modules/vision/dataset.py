"""
SpaceLoop Vision Paired Dataset Loader
======================================
Manages loading, validation, and metadata for paired BEFORE and AFTER room condition images.

Supported Labels:
    1. CLEAN: Room is in identical condition; furniture unchanged, appliances off, zero waste.
    2. MINOR_CHANGE: Minor permissible shift (e.g., chair adjusted slightly, personal water bottle removed).
    3. SIGNIFICANT_CHANGE: Lights or fans left running, visible surface trash, or unarranged furniture.
    4. DAMAGE: Structural damage, carpet/wall stains, broken fixtures, or physical property defects.

Directory Structure Expected:
    backend/modules/vision/dataset/
    ├── CLEAN/
    │   ├── pair_001_before.jpg
    │   └── pair_001_after.jpg
    ├── MINOR_CHANGE/
    │   ├── pair_002_before.jpg
    │   └── pair_002_after.jpg
    ├── SIGNIFICANT_CHANGE/
    │   ├── pair_003_before.jpg
    │   └── pair_003_after.jpg
    └── DAMAGE/
        ├── pair_004_before.jpg
        └── pair_004_after.jpg
"""

from typing import List, Dict, Optional, Tuple, Set
import os
import glob
import json
import csv
from dataclasses import dataclass
from PIL import Image

SUPPORTED_LABELS: List[str] = [
    "CLEAN",
    "MINOR_CHANGE",
    "SIGNIFICANT_CHANGE",
    "DAMAGE",
]

LABEL_TO_ID: Dict[str, int] = {
    "CLEAN": 0,
    "MINOR_CHANGE": 1,
    "SIGNIFICANT_CHANGE": 2,
    "DAMAGE": 3,
}

ID_TO_LABEL: Dict[int, str] = {v: k for k, v in LABEL_TO_ID.items()}

VALID_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass
class PairSample:
    """Represents a single verified before-and-after room condition sample."""
    pair_id: str
    before_path: str
    after_path: str
    label: str
    label_id: int

    def validate(self) -> bool:
        """Verifies that both files exist and are valid decodable images."""
        if not os.path.isfile(self.before_path):
            raise FileNotFoundError(f"Missing before image: {self.before_path}")
        if not os.path.isfile(self.after_path):
            raise FileNotFoundError(f"Missing after image: {self.after_path}")

        with Image.open(self.before_path) as img:
            img.verify()
        with Image.open(self.after_path) as img:
            img.verify()

        return True


def _match_pair_files(files: List[str]) -> List[Tuple[str, str, str]]:
    """
    Finds matching before and after image files from a list of file paths.
    Supports conventions:
        - {id}_before.ext and {id}_after.ext
        - {id}_entry.ext and {id}_exit.ext
        - {id}_pre.ext and {id}_post.ext
    Returns list of (pair_id, before_file, after_file).
    """
    before_map: Dict[str, str] = {}
    after_map: Dict[str, str] = {}

    for fpath in files:
        fname = os.path.basename(fpath)
        base, ext = os.path.splitext(fname)
        ext_lower = ext.lower()
        if ext_lower not in VALID_IMAGE_EXTENSIONS:
            continue

        base_lower = base.lower()
        # Suffix matching
        for b_suffix, a_suffix in [("_before", "_after"), ("-before", "-after"),
                                   ("_entry", "_exit"), ("-entry", "-exit"),
                                   ("_pre", "_post"), ("-pre", "-post")]:
            if base_lower.endswith(b_suffix):
                prefix = base[:len(base) - len(b_suffix)]
                before_map[prefix] = fpath
                break
            elif base_lower.endswith(a_suffix):
                prefix = base[:len(base) - len(a_suffix)]
                after_map[prefix] = fpath
                break

    matched_pairs: List[Tuple[str, str, str]] = []
    common_ids = sorted(set(before_map.keys()) & set(after_map.keys()))
    for cid in common_ids:
        matched_pairs.append((cid, before_map[cid], after_map[cid]))

    return matched_pairs


def _load_from_class_subdirectories(dataset_dir: str) -> List[PairSample]:
    """Loads paired samples from CLEAN/, MINOR_CHANGE/, SIGNIFICANT_CHANGE/, DAMAGE/."""
    samples: List[PairSample] = []

    for label in SUPPORTED_LABELS:
        class_dir = os.path.join(dataset_dir, label)
        if not os.path.isdir(class_dir):
            continue

        # Strategy 1: Look for {id}_before and {id}_after in class_dir directly
        all_files = [os.path.join(class_dir, f) for f in os.listdir(class_dir) if os.path.isfile(os.path.join(class_dir, f))]
        matched = _match_pair_files(all_files)
        for pair_id, b_path, a_path in matched:
            samples.append(PairSample(
                pair_id=f"{label}_{pair_id}",
                before_path=b_path,
                after_path=a_path,
                label=label,
                label_id=LABEL_TO_ID[label],
            ))

        # Strategy 2: Look for subdirectories under class_dir (e.g. class_dir/pair_01/before.jpg)
        subdirs = [os.path.join(class_dir, d) for d in os.listdir(class_dir) if os.path.isdir(os.path.join(class_dir, d))]
        for sdir in subdirs:
            s_name = os.path.basename(sdir)
            b_cand = None
            a_cand = None
            for ext in VALID_IMAGE_EXTENSIONS:
                for b_name in [f"before{ext}", f"entry{ext}", f"pre{ext}"]:
                    p = os.path.join(sdir, b_name)
                    if os.path.isfile(p):
                        b_cand = p
                        break
                for a_name in [f"after{ext}", f"exit{ext}", f"post{ext}"]:
                    p = os.path.join(sdir, a_name)
                    if os.path.isfile(p):
                        a_cand = p
                        break

            if b_cand and a_cand:
                samples.append(PairSample(
                    pair_id=f"{label}_{s_name}",
                    before_path=b_cand,
                    after_path=a_cand,
                    label=label,
                    label_id=LABEL_TO_ID[label],
                ))

    return samples


def _load_from_manifest(manifest_path: str, dataset_root: str) -> List[PairSample]:
    """Loads pairs defined explicitly in a manifest.json or manifest.csv."""
    samples: List[PairSample] = []

    if manifest_path.endswith(".json"):
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("samples", [])
        for item in records:
            lbl = item.get("label", "").upper().strip()
            if lbl not in LABEL_TO_ID:
                continue
            b_path = item.get("before_image") or item.get("before_path")
            a_path = item.get("after_image") or item.get("after_path")
            if not os.path.isabs(b_path):
                b_path = os.path.join(dataset_root, b_path)
            if not os.path.isabs(a_path):
                a_path = os.path.join(dataset_root, a_path)
            samples.append(PairSample(
                pair_id=str(item.get("pair_id") or os.path.basename(b_path)),
                before_path=b_path,
                after_path=a_path,
                label=lbl,
                label_id=LABEL_TO_ID[lbl],
            ))

    elif manifest_path.endswith(".csv"):
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lbl = (row.get("label") or "").upper().strip()
                if lbl not in LABEL_TO_ID:
                    continue
                b_path = row.get("before_image") or row.get("before_path")
                a_path = row.get("after_image") or row.get("after_path")
                if not os.path.isabs(b_path):
                    b_path = os.path.join(dataset_root, b_path)
                if not os.path.isabs(a_path):
                    a_path = os.path.join(dataset_root, a_path)
                samples.append(PairSample(
                    pair_id=str(row.get("pair_id") or os.path.basename(b_path)),
                    before_path=b_path,
                    after_path=a_path,
                    label=lbl,
                    label_id=LABEL_TO_ID[lbl],
                ))

    return samples


def load_paired_dataset(dataset_dir: str) -> List[PairSample]:
    """
    Scans and validates all paired images inside dataset_dir.
    Checks class subdirectories first, then manifest.json / manifest.csv if present.
    """
    if not os.path.isdir(dataset_dir):
        return []

    # 1. Check manifests first
    json_man = os.path.join(dataset_dir, "manifest.json")
    csv_man = os.path.join(dataset_dir, "manifest.csv")
    if os.path.isfile(json_man):
        samples = _load_from_manifest(json_man, dataset_dir)
        if samples:
            return samples
    if os.path.isfile(csv_man):
        samples = _load_from_manifest(csv_man, dataset_dir)
        if samples:
            return samples

    # 2. Check class subdirectories
    return _load_from_class_subdirectories(dataset_dir)


def get_dataset_class_counts(samples: List[PairSample]) -> Dict[str, int]:
    """Returns distribution of samples across the supported labels."""
    counts = {lbl: 0 for lbl in SUPPORTED_LABELS}
    for s in samples:
        counts[s.label] += 1
    return counts
