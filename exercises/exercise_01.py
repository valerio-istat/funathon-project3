# %%
# Exercise 1 - Read a Sentinel-2 tile and display it
import matplotlib.pyplot as plt
import numpy as np
import rasterio

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

with rasterio.open(TILE_URL) as src:
    rgb_data = src.read([4, 3, 2])
    tile_crs = src.crs
    tile_bounds = src.bounds

print(f"CRS: {tile_crs}")
print(f"Bounds: {tile_bounds}")

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
