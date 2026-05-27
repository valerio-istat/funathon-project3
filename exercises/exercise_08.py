# %%
# Exercise 8 - Display a Sentinel-2 tile on an interactive folium map
import folium
import numpy as np
import rasterio
from rasterio.warp import transform_bounds

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

with rasterio.open(TILE_URL) as src:
    tile_bounds = src.bounds
    tile_crs = src.crs
    rgb_data = src.read([4, 3, 2])

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

west, south, east, north = transform_bounds(tile_crs, "EPSG:4326", *tile_bounds)
center_lat = (south + north) / 2
center_lon = (west + east) / 2

m8 = folium.Map(location=[center_lat, center_lon], zoom_start=14)
folium.raster_layers.ImageOverlay(
    image=rgb,
    bounds=[[south, west], [north, east]],
    opacity=0.7,
).add_to(m8)
m8.save("exercise8_map.html")
m8

# %%
