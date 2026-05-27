# %%
# Exercise 6 - Build a GeoDataFrame from tile bounds and convert CRS
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from shapely.geometry import box

TILE_CODE = "LU000"
TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)


def read_tile_footprint(tile_url: str, tile_code: str) -> gpd.GeoDataFrame:
    with rasterio.open(tile_url) as src:
        tile_geom = box(*src.bounds)
        tile_crs = src.crs
    return gpd.GeoDataFrame(
        {"tile": [tile_code]},
        geometry=[tile_geom],
        crs=tile_crs,
    )


def read_rgb(tile_url: str) -> tuple[np.ndarray, list[float]]:
    with rasterio.open(tile_url) as src:
        rgb_data = src.read([4, 3, 2])
        bounds = src.bounds

    rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
    rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    return rgb, extent


tile_gdf = read_tile_footprint(TILE_URL, TILE_CODE)
tile_wgs84 = tile_gdf.to_crs("EPSG:4326")
rgb, extent = read_rgb(TILE_URL)

area_km2 = tile_gdf.geometry.area.iloc[0] / 1_000_000

print("Source CRS:", tile_gdf.crs)
print("EPSG:3035 bounds:", tile_gdf.total_bounds)
print("EPSG:4326 bounds:", tile_wgs84.total_bounds)
print(f"Tile area: {area_km2:.2f} km^2")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(rgb, extent=extent)
tile_gdf.boundary.plot(ax=axes[0], color="red", linewidth=2)
axes[0].set_title("Sentinel-2 tile with boundary overlay")
axes[0].set_xlabel("Easting (m)")
axes[0].set_ylabel("Northing (m)")

tile_wgs84.plot(ax=axes[1], color="none", edgecolor="tab:green", linewidth=2)
axes[1].set_title("Footprint in EPSG:4326")
axes[1].set_xlabel("longitude")
axes[1].set_ylabel("latitude")

for ax in axes:
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.25)

plt.tight_layout()
plt.show()

# %%
