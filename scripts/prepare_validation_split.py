from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create deterministic validation and final-test holdouts from an MVTec-style test directory."
    )
    parser.add_argument("--test-dir", required=True, help="Original category test directory.")
    parser.add_argument("--output-dir", required=True, help="Directory that will contain validation/ and final_test/.")
    parser.add_argument("--validation-ratio", type=float, default=0.40)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def images_in(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def main() -> None:
    args = parse_args()
    if not 0.0 < args.validation_ratio < 1.0:
        raise SystemExit("--validation-ratio must be strictly between 0 and 1.")

    source = Path(args.test_dir)
    output = Path(args.output_dir)
    validation_root = output / "validation"
    final_root = output / "final_test"
    rng = random.Random(args.seed)

    if not source.exists():
        raise SystemExit(f"Test directory does not exist: {source}")

    summary: dict[str, dict[str, int]] = {}

    for defect_dir in sorted(p for p in source.iterdir() if p.is_dir()):
        images = images_in(defect_dir)
        if len(images) < 2:
            raise SystemExit(
                f"Folder '{defect_dir.name}' has fewer than two images; "
                "cannot create both validation and final-test holdouts."
            )

        shuffled = images[:]
        rng.shuffle(shuffled)
        n_validation = max(1, min(len(shuffled) - 1, round(len(shuffled) * args.validation_ratio)))
        validation_images = shuffled[:n_validation]
        final_images = shuffled[n_validation:]

        for split_root, selected in (
            (validation_root, validation_images),
            (final_root, final_images),
        ):
            target_dir = split_root / defect_dir.name
            target_dir.mkdir(parents=True, exist_ok=True)
            for image in selected:
                shutil.copy2(image, target_dir / image.name)

        summary[defect_dir.name] = {
            "source": len(images),
            "validation": len(validation_images),
            "final_test": len(final_images),
        }

    metadata = {
        "source_test_dir": str(source),
        "validation_ratio": args.validation_ratio,
        "seed": args.seed,
        "strategy": "Deterministic stratified split by original test subfolder",
        "warning": (
            "This creates a project-specific validation/final-test protocol from the official benchmark test set. "
            "Report this explicitly rather than claiming the untouched official benchmark protocol."
        ),
        "counts": summary,
    }

    output.mkdir(parents=True, exist_ok=True)
    (output / "split_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
