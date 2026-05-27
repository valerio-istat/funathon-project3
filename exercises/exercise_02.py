# %%
# Exercise 2 - Explore raster metadata and create a false-colour composite
import matplotlib.pyplot as plt
import numpy as np
import rasterio

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

with rasterio.open(TILE_URL) as src:
    print(src.profile)
    rgb_data = src.read([4, 3, 2])
    fc_data = src.read([8, 4, 3])  # NIR, Red, Green

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fc = np.transpose(fc_data, (1, 2, 0)).astype(np.float32)
fc = np.clip(fc / np.percentile(fc, 98), 0, 1)

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(rgb)
axes[0].set_title("True colour (B4, B3, B2)")
axes[0].axis("off")
axes[1].imshow(fc)
axes[1].set_title("False colour (B8, B4, B3)")
axes[1].axis("off")
plt.tight_layout()
plt.show()

# %%
