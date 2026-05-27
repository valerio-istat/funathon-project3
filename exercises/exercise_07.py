# %%
# Exercise 7 - Spatial join and intersection with NUTS3 regions
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
NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)


def read_tile_footprint(tile_url: str, tile_code: str) -> gpd.GeoDataFrame:
    with rasterio.open(tile_url) as src:
        return gpd.GeoDataFrame(
            {"tile": [tile_code]},
            geometry=[box(*src.bounds)],
            crs=src.crs,
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
rgb, extent = read_rgb(TILE_URL)
nuts = gpd.read_file(NUTS_URL).to_crs(tile_gdf.crs)

joined = gpd.sjoin(tile_gdf, nuts, predicate="intersects")
if joined.empty:
    raise RuntimeError("The tile footprint does not intersect any NUTS3 region.")

intersections = gpd.overlay(
    tile_gdf,
    nuts[["NUTS_ID", "NUTS_NAME", "geometry"]],
    how="intersection",
)
intersections["intersection_km2"] = intersections.geometry.area / 1_000_000
tile_area_km2 = tile_gdf.geometry.area.iloc[0] / 1_000_000
intersections["share_pct"] = intersections["intersection_km2"] / tile_area_km2 * 100

summary = (
    intersections[["NUTS_ID", "NUTS_NAME", "intersection_km2", "share_pct"]]
    .sort_values("intersection_km2", ascending=False)
    .reset_index(drop=True)
)

print(f"Tile area: {tile_area_km2:.2f} km^2")
for _, row in joined.iterrows():
    print(f"NUTS_ID: {row['NUTS_ID']}, NUTS_NAME: {row['NUTS_NAME']}")
print(summary.to_string(index=False, formatters={
    "intersection_km2": "{:.3f}".format,
    "share_pct": "{:.2f}".format,
}))

fig, ax = plt.subplots(figsize=(7, 7))
ax.imshow(rgb, extent=extent)
nearby_nuts = nuts[nuts.intersects(tile_gdf.buffer(20_000).geometry.iloc[0])]
nearby_nuts.boundary.plot(ax=ax, color="lightgray", linewidth=1)
intersections.plot(ax=ax, color="none", edgecolor="tab:orange", linewidth=3)
tile_gdf.boundary.plot(ax=ax, color="red", linewidth=2, linestyle="--")
tile_gdf.centroid.plot(ax=ax, color="black", markersize=20)

minx, miny, maxx, maxy = tile_gdf.total_bounds
padding = 1_000
ax.set_xlim(minx - padding, maxx + padding)
ax.set_ylim(miny - padding, maxy + padding)
ax.set_title("Sentinel-2 tile with NUTS3 intersection")
ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.set_aspect("equal", adjustable="box")
plt.tight_layout()
plt.show()

# %%
