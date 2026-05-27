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

    # Step 2b: Read false-colour bands (NIR=8, Red=4, Green=3)
    fc_data = src.read([8, 4, 3]) 
    rgb_data = src.read([4, 3, 2])

# Step 2c: Normalize for display
fc = np.transpose(fc_data, (1, 2, 0)).astype(np.float32)
rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(rgb, 98) 
rgb = np.clip(rgb / p98, 0, 1) 
p98 = np.percentile(fc, 98) 
fc = np.clip(fc / p98, 0, 1) 

# Step 2d: Display side by side with the true-colour RGB
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
