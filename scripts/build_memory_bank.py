from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.models import Wide_ResNet50_2_Weights, wide_resnet50_2
from torchvision.models.feature_extraction import create_feature_extractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normal-only deep feature memory bank.")
    parser.add_argument("--train-dir", required=True, help="Directory containing normal training images.")
    parser.add_argument("--output", required=True, help="Output .pt memory bank path.")
    parser.add_argument("--sample-ratio", type=float, default=0.20, help="Fraction of patches retained per image.")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_dir = Path(args.train_dir)
    paths = sorted([p for p in train_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
    if not paths:
        raise SystemExit(f"No images found in {train_dir}")

    backbone = wide_resnet50_2(weights=Wide_ResNet50_2_Weights.IMAGENET1K_V1).to(device).eval()
    extractor = create_feature_extractor(backbone, return_nodes={"layer2": "layer2", "layer3": "layer3"})
    transform = T.Compose(
        [
            T.Resize((256, 256)),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    banks = []
    with torch.no_grad():
        for path in paths:
            tensor = transform(Image.open(path).convert("RGB")).unsqueeze(0).to(device)
            feats = extractor(tensor)
            f2, f3 = feats["layer2"], feats["layer3"]
            f3 = F.interpolate(f3, size=f2.shape[2:], mode="bilinear", align_corners=False)
            fused = torch.cat([f2, f3], dim=1)
            patches = fused.squeeze(0).permute(1, 2, 0).reshape(-1, fused.shape[1])
            keep = max(1, int(len(patches) * args.sample_ratio))
            indices = torch.randperm(len(patches), device=device)[:keep]
            banks.append(patches[indices].cpu())

    memory_bank = torch.cat(banks, dim=0)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(memory_bank, output)

    metadata = {
        "num_training_images": len(paths),
        "num_patches": int(memory_bank.shape[0]),
        "feature_dim": int(memory_bank.shape[1]),
        "sample_ratio": args.sample_ratio,
        "seed": args.seed,
        "device_used": str(device),
    }
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
