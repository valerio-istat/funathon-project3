import os
import urllib.request
import rasterio
import numpy as np

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    tile_crs = src.crs
    tile_bounds = src.bounds
    tile_count = src.count
    tile_height = src.height
    tile_width = src.width
    tile_profile = src.profile
    # Read RGB bands: B4 (Red), B3 (Green), B2 (Blue)
    rgb_data = src.read([4, 3, 2])
    false_color_data = src.read([8, 4, 3])

print(f"CRS:    {tile_crs}")
print(f"Bounds: {tile_bounds}")
print(f"Shape:  {tile_count} bands x {tile_height} x {tile_width} px")
print(f"Profile: {tile_profile}")
# your code here …

# %%
import matplotlib.pyplot as plt

# Transpose to (H, W, 3) and normalize for display
rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
false_color = np.transpose(false_color_data, (1, 2, 0)).astype(np.float32)

rgb_pct = np.percentile(rgb, 98)
false_pct = np.percentile(false_color, 98)

rgb = np.clip(rgb / rgb_pct, 0, 1)
false_color = np.clip(false_color / false_pct, 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite (B4, B3, B2) — LU000")
ax.axis("off")
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(false_color)
ax.set_title("Sentinel-2 False color composite (B8, B4, B3) — LU000")
ax.axis("off")
plt.tight_layout()
plt.show()
