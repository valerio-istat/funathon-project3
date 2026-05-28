# %%
# Exercise 11 - 2-model.qmd hands-on (parameter exploration + forward anatomy)
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

# Ensure project root is on PYTHONPATH when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model import SegformerB5  # noqa: E402


def count_params(module):
    total = sum(p.numel() for p in module.parameters())
    trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
    return total, trainable


def main():
    print("Loading SegFormer MiT-B5 (this may download weights on first run)...")
    model = SegformerB5(
        n_bands=14,
        logits=True,
        freeze_encoder=False,
    )

    # ---- Exercise 1: Parameter exploration ---------------------------------
    total, trainable = count_params(model)
    enc_total, enc_trainable = count_params(model.segformer)
    dec_total, dec_trainable = count_params(model.decode_head)

    print(f"\n{'Component':<20} {'Total params':>15} {'Trainable params':>18}")
    print("-" * 55)
    print(f"{'Encoder (MiT-B5)':<20} {enc_total:>15,} {enc_trainable:>18,}")
    print(f"{'Decoder (MLP)':<20} {dec_total:>15,} {dec_trainable:>18,}")
    print(f"{'Full model':<20} {total:>15,} {trainable:>18,}")

    print("\nEncoder stages:")
    stage_sizes = []
    for i, stage in enumerate(model.segformer.encoder.block):
        n = sum(p.numel() for p in stage.parameters())
        stage_sizes.append((i + 1, n))
        print(f"Stage {i + 1}: {n:,} parameters")

    biggest_stage = max(stage_sizes, key=lambda x: x[1])
    print(f"Stage with most parameters: Stage {biggest_stage[0]} ({biggest_stage[1]:,})")

    print("\nDecoder projections:")
    for i, proj in enumerate(model.decode_head.linear_c):
        n = sum(p.numel() for p in proj.parameters())
        print(f"Projection {i + 1}: {n:,} parameters")

    clf_params = sum(p.numel() for p in model.decode_head.classifier.parameters())
    clf_frac = 100 * clf_params / dec_total
    print(f"Classifier: {clf_params:,} / {dec_total:,} ({clf_frac:.2f}%)")

    # ---- Exercise 2: Forward pass anatomy ----------------------------------
    B, C, H, W = 2, 14, 512, 512
    dummy_input = torch.randn(B, C, H, W)
    dummy_labels = torch.randint(0, model.config.num_labels, (B, H, W))

    model.eval()
    with torch.no_grad():
        logits = model(dummy_input)  # (B, K, H/4, W/4)
        upsampled_direct = model(dummy_input, dummy_labels)  # (B, K, H, W)
        hidden_outputs = model.segformer(
            dummy_input,
            output_hidden_states=True,
            return_dict=True,
        )

    logits_full = F.interpolate(
        logits,
        size=(H, W),
        mode="bilinear",
        align_corners=False,
    )
    probs = torch.softmax(logits_full, dim=1)
    pred = torch.argmax(probs, dim=1)

    print("\nForward pass shapes:")
    print(f"Input:               {tuple(dummy_input.shape)}")
    print(f"Labels:              {tuple(dummy_labels.shape)}")
    print(f"Logits (no labels):  {tuple(logits.shape)}")
    print(f"Manual upsample:     {tuple(logits_full.shape)}")
    print(f"Model with labels:   {tuple(upsampled_direct.shape)}")
    print(f"Predicted map:       {tuple(pred.shape)}")
    print(f"Unique classes pred: {pred.unique().tolist()}")

    same_shape = logits_full.shape == upsampled_direct.shape
    print(f"Manual upsample shape == model-with-labels shape: {same_shape}")

    print("\nHidden states and area ratios:")
    for i, hs in enumerate(hidden_outputs.hidden_states):
        ratio = (hs.shape[-2] * hs.shape[-1]) / (H * W)
        print(f"Stage {i + 1}: shape={tuple(hs.shape)} area_ratio={ratio:.6f}")

    # Freeze/unfreeze quick check from the chapter
    model.freeze()
    _, trainable_frozen = count_params(model)
    model.unfreeze()
    _, trainable_unfrozen = count_params(model)
    print("\nFreeze/unfreeze check:")
    print(f"Trainable after freeze:   {trainable_frozen:,}")
    print(f"Trainable after unfreeze: {trainable_unfrozen:,}")


if __name__ == "__main__":
    main()

# %%
