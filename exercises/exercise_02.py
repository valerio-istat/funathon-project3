# %%
# Exercise 2 - Explore raster metadata and create Sentinel-2 composites
import matplotlib.pyplot as plt
import numpy as np
import rasterio

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

COMPOSITES = {
    "True colour\nB4, B3, B2": (4, 3, 2),
    "False colour vegetation\nB8, B4, B3": (8, 4, 3),
    "SWIR urban\nB11, B8, B4": (11, 8, 4),
}


def robust_display(image: np.ndarray, low: float = 2, high: float = 98) -> np.ndarray:
    output = np.empty_like(image, dtype=np.float32)
    for channel in range(image.shape[-1]):
        lo, hi = np.percentile(image[..., channel], [low, high])
        if hi <= lo:
            output[..., channel] = 0
        else:
            output[..., channel] = np.clip((image[..., channel] - lo) / (hi - lo), 0, 1)
    return output


def read_composite(src: rasterio.io.DatasetReader, bands: tuple[int, int, int]) -> np.ndarray:
    data = src.read(list(bands)).astype(np.float32)
    image = np.transpose(data, (1, 2, 0))
    return robust_display(image)


with rasterio.open(TILE_URL) as src:
    metadata = {
        "crs": src.crs,
        "bounds": src.bounds,
        "shape": (src.height, src.width),
        "band_count": src.count,
        "dtype": src.dtypes[0],
        "transform": src.transform,
    }
    composites = {
        title: read_composite(src, bands)
        for title, bands in COMPOSITES.items()
    }

for key, value in metadata.items():
    print(f"{key}: {value}")

fig, axes = plt.subplots(1, len(composites), figsize=(15, 5))
for ax, (title, image) in zip(axes, composites.items(), strict=True):
    ax.imshow(image)
    ax.set_title(title)
    ax.axis("off")

plt.tight_layout()
plt.show()

# %%
