# %%
# Exercise 1 - Build a 14-band Sentinel-2 patch over Rome and display RGB
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.windows import bounds as window_bounds
from rasterio.warp import transform

PRODUCT_BASE_URL = (
    "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/"
    "33/T/TG/2024/9/S2A_33TTG_20240921_0_L2A"
)
ROME_LON = 12.4964
ROME_LAT = 41.9028
WINDOW_SIZE = 512

S2_BANDS = [
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B09",
    "B11",
    "B12",
]

# Use B04 as reference grid (10m) to extract a centered patch over Rome.
with rasterio.open(f"{PRODUCT_BASE_URL}/B04.tif") as ref:
    x_rome, y_rome = transform("EPSG:4326", ref.crs, [ROME_LON], [ROME_LAT])
    row, col = ref.index(x_rome[0], y_rome[0])
    half = WINDOW_SIZE // 2
    row_off = max(0, min(ref.height - WINDOW_SIZE, row - half))
    col_off = max(0, min(ref.width - WINDOW_SIZE, col - half))
    ref_window = Window(col_off=col_off, row_off=row_off, width=WINDOW_SIZE, height=WINDOW_SIZE)
    patch_bounds = window_bounds(ref_window, ref.transform)
    tile_crs = ref.crs
    tile_bounds = patch_bounds

stack_12 = []
for band in S2_BANDS:
    band_url = f"{PRODUCT_BASE_URL}/{band}.tif"
    with rasterio.open(band_url) as src:
        band_window = src.window(*patch_bounds)
        band_data = src.read(
            1,
            window=band_window,
            out_shape=(WINDOW_SIZE, WINDOW_SIZE),
            resampling=Resampling.bilinear,
        ).astype(np.float32)
        stack_12.append(band_data)

stack_12 = np.stack(stack_12, axis=0)

red = stack_12[S2_BANDS.index("B04")]
green = stack_12[S2_BANDS.index("B03")]
blue = stack_12[S2_BANDS.index("B02")]
nir = stack_12[S2_BANDS.index("B08")]

ndvi = np.where(nir + red == 0, 0, (nir - red) / (nir + red))
ndwi = np.where(green + nir == 0, 0, (green - nir) / (green + nir))

image_14bands = np.concatenate([stack_12, ndvi[None, ...], ndwi[None, ...]], axis=0)

print(f"CRS: {tile_crs}")
print(f"Bounds: {tile_bounds}")
print(f"14-band image shape (bands, y, x): {image_14bands.shape}")

rgb = np.stack([red, green, blue], axis=-1).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite - Rome (from 14-band stack)")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
