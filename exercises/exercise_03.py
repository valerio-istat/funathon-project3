# %%
# Exercise 3 - Compute and display NDVI
import matplotlib.pyplot as plt
import numpy as np
import rasterio

RED_BAND = 4
NIR_BAND = 8

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)


def compute_ndvi(red: np.ma.MaskedArray, nir: np.ma.MaskedArray) -> np.ma.MaskedArray:
    denominator = nir + red
    ndvi = np.ma.divide(nir - red, denominator)
    return np.ma.masked_where(denominator == 0, ndvi)


with rasterio.open(TILE_URL) as src:
    red = src.read(RED_BAND, masked=True).astype(np.float32)
    nir = src.read(NIR_BAND, masked=True).astype(np.float32)
    tile_crs = src.crs
    tile_bounds = src.bounds

ndvi = compute_ndvi(red, nir)
valid_ndvi = ndvi.compressed()

print(f"CRS: {tile_crs}")
print(f"Bounds: {tile_bounds}")
print(f"Valid pixels: {valid_ndvi.size}")
print(
    "NDVI percentiles "
    f"(p05, p50, p95): {np.percentile(valid_ndvi, [5, 50, 95]).round(3)}"
)

extent = [tile_bounds.left, tile_bounds.right, tile_bounds.bottom, tile_bounds.top]

fig, (map_ax, hist_ax) = plt.subplots(1, 2, figsize=(11, 5))
im = map_ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1, extent=extent)
map_ax.set_title("NDVI - LU000 (2024)")
map_ax.set_xlabel(f"x ({tile_crs})")
map_ax.set_ylabel(f"y ({tile_crs})")
fig.colorbar(im, ax=map_ax, shrink=0.8, label="NDVI")

hist_ax.hist(valid_ndvi, bins=60, range=(-1, 1), color="#4C7C59", edgecolor="white")
hist_ax.set_title("NDVI distribution")
hist_ax.set_xlabel("NDVI")
hist_ax.set_ylabel("Pixel count")
hist_ax.set_xlim(-1, 1)

plt.tight_layout()
plt.show()

# %%
