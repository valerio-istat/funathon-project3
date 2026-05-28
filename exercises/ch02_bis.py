# %%
import sys
from pathlib import Path
 
import torch
import torch.nn.functional as F

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model import SegformerB5

# This downloads ~330 MB of weights from HuggingFace on first run
model = SegformerB5(
    # 14 matches the layout of the pre-baked GeoTIFFs: the 12 L2A spectral bands
    # (B10 is dropped by atmospheric correction) plus NDVI and NDWI as derived
    # channels. `src/download_region.py` produces the same layout. If you swap in
    # a different dataset (different band count or different derived layers), this
    # number, the normalisation statistics, and `num_channels` in the SegformerConfig
    # must all change together — otherwise the first patch-embedding layer
    # mis-shapes inputs.
    n_bands=14,
    logits=True,             # return raw logits (not probabilities)
    freeze_encoder=False,    # keep encoder trainable
    type_labeler="CLCplus-Backbone",
)

# %%
def count_params(module):
    total = sum(p.numel() for p in module.parameters())
    trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
    return total, trainable

# %%
total, trainable = count_params(model)
enc_total, enc_trainable = count_params(model.segformer)
dec_total, dec_trainable = count_params(model.decode_head)

print(f"{'Component':<20} {'Total params':>15} {'Trainable params':>18}")
print("-" * 55)
print(f"{'Encoder (MiT-B5)':<20} {enc_total:>15,} {enc_trainable:>18,}")
print(f"{'Decoder (MLP)':<20} {dec_total:>15,} {dec_trainable:>18,}")
print(f"{'Full model':<20} {total:>15,} {trainable:>18,}")# %%

# %%
# Freeze all encoder parameters
model.freeze()

total, trainable = count_params(model)
print(f"After freezing encoder — trainable: {trainable:,} / {total:,}")

# Unfreeze for full fine-tuning
model.unfreeze()
total, trainable = count_params(model)
print(f"After unfreezing — trainable: {trainable:,} / {total:,}")
# %%
# 1. Parameters per encoder stage.
# Deeper stages have more channels (C₁ < C₂ < C₃ < C₄), so even with fewer transformer
# blocks they end up holding most of the encoder's capacity. This matters during
# fine-tuning: freezing stages 3–4 alone already locks the bulk of the model's weights.
for i, stage in enumerate(model.segformer.encoder.block):
    n = sum(p.numel() for p in stage.parameters())
    print(f"Stage {i+1}: {n:,} parameters")

# 2. Decoder breakdown.
# The four projection layers are tiny linear maps (one per encoder stage); the real
# decoder cost lives in the linear_fuse + classifier. Seeing how light the head is
# explains why training the decoder alone is fast and resistant to overfitting.
for i, proj in enumerate(model.decode_head.linear_c):
    n = sum(p.numel() for p in proj.parameters())
    print(f"Decoder projection {i+1}: {n:,} parameters")

clf_params = sum(p.numel() for p in model.decode_head.classifier.parameters())
dec_total = sum(p.numel() for p in model.decode_head.parameters())
print(f"Classifier: {clf_params:,} / {dec_total:,} decoder params "
      f"({100*clf_params/dec_total:.1f}%)")
# %%
import torch

B, C, H, W = 2, 14, 512, 512   # batch size, channels, height, width
dummy_input = torch.randn(B, C, H, W)
dummy_labels = torch.randint(0, model.config.num_labels, (B, H, W))

print(f"Input  shape: {tuple(dummy_input.shape)}")
print(f"Labels shape: {tuple(dummy_labels.shape)}")
# %%
import torch.nn.functional as F

model.eval()
with torch.no_grad():
    # Logits = raw, unbounded per-class scores. They have shape (B, num_classes, H/4, W/4)
    # because the all-MLP decoder fuses everything at the finest encoder scale (H/4).
    logits = model(dummy_input)
    # output_hidden_states=True surfaces the four encoder feature maps. The decoder
    # combines all four — early stages (high resolution) carry local detail, late
    # stages (low resolution) carry semantic context. Returning them is what makes
    # multi-scale fusion possible.
    outputs = model.segformer(
        dummy_input, output_hidden_states=True, return_dict=True
    )

# 1. Manual upsampling.
# Bilinear (not nearest-neighbour) because logits are continuous scores: interpolating
# between two scores is meaningful, whereas a discrete class label is not.
logits_full = F.interpolate(
    logits,
    size=(H, W),
    mode="bilinear",
    align_corners=False,
)
print(f"Manually upsampled: {tuple(logits_full.shape)}")

# 2. Predicted class map.
# softmax converts logits → probabilities; argmax picks the most likely class at each
# pixel. The class axis disappears: (B, num_classes, H, W) → (B, H, W), one int per pixel.
probs = torch.softmax(logits_full, dim=1)
pred  = torch.argmax(probs, dim=1)
print(f"Predicted map shape: {tuple(pred.shape)}")
print(f"Unique predicted classes: {pred.unique().tolist()}")

# 3. Spatial area ratios — stage 1 is at H/4 × W/4 → 1/16 of the input area, and each
# next stage divides that by 4 again (1/64, 1/256, 1/1024).
for i, hs in enumerate(outputs.hidden_states):
    ratio = (hs.shape[-2] * hs.shape[-1]) / (H * W)
    print(f"Stage {i+1}: {ratio:.4f}")
# %%
from src.models.module import SegmentationModule
from torch import nn, optim

module = SegmentationModule(
    model=model,
    loss=nn.CrossEntropyLoss(ignore_index=255),
    optimizer=optim.AdamW,
    optimizer_params={"lr": 1e-3, "weight_decay": 1e-2},
    scheduler=optim.lr_scheduler.OneCycleLR,
    scheduler_params={},
    scheduler_interval="step",
)
# %%
from src.training.metrics import IOU, positive_rate

# Simulate model output and labels
B, num_classes, H, W = 2, 11, 512, 512
dummy_logits = torch.randn(B, num_classes, H, W)
dummy_labels = torch.randint(0, num_classes, (B, H, W))

iou_mean, iou_building = IOU(dummy_logits, dummy_labels, logits=True)
building_rate = positive_rate(dummy_logits, logits=True)

print(f"Mean IoU:      {iou_mean:.4f}")
print(f"Building IoU:  {iou_building:.4f}")
print(f"Building rate: {building_rate:.4f}  (fraction of pixels predicted as building)")
# %%
