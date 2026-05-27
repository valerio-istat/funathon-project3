# %%
# Exercise 3 - Compute and display NDVI
import matplotlib.pyplot as plt
import numpy as np
import rasterio

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

with rasterio.open(TILE_URL) as src:
    nir = src.read(8).astype(np.float32)
    red = src.read(4).astype(np.float32)

ndvi = np.where(nir + red == 0, 0, (nir - red) / (nir + red))

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
ax.set_title("NDVI - LU000 (2024)")
ax.axis("off")
fig.colorbar(im, ax=ax, shrink=0.8, label="NDVI")
plt.tight_layout()
plt.show()
