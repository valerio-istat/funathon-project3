# %%

import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

# Step 2a: Open the tile and print the raster profile
with rasterio.open(tile_url) as src:
    print(src.profile)

    # Step 2b: Read NIR and red bands (NIR=8, Red=4)
    ndvi_data = src.read([8, 4])
    nir_data = ndvi_data[0]
    red_data = ndvi_data[1]

# Step 2c: Normalize for display
ndvi = np.where(nir_data + red_data == 0, 0, (nir_data - red_data)/(nir_data + red_data))

# Step 2d: Display side by side with the true-colour RGB
fig, ax = plt.subplots(figsize=(5, 5))

im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
fig.colorbar(im, ax=ax, shrink=0.6, label="NDVI")
ax.set_title("NVDI index — LU000")
ax.axis("off")
plt.tight_layout()
plt.show()
# %%
