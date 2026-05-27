# %%
# Exercise 10 - Overlay satellite image and CLC+ label on an interactive map
import io
import urllib.request

import folium
import numpy as np
import rasterio
from matplotlib.colors import to_rgba
from rasterio.warp import transform_bounds

classes10 = [
    ("Sealed (1)", "#FF0100"),
    ("Woody -- needle leaved trees (2)", "#238B23"),
    ("Woody -- Broadleaved deciduous trees (3)", "#80FF00"),
    ("Woody -- Broadleaved evergreen trees (4)", "#00FF00"),
    ("Low-growing woody plants (bushes, shrubs) (5)", "#804000"),
    ("Permanent herbaceous (6)", "#CCF24E"),
    ("Periodically herbaceous (7)", "#FEFF80"),
    ("Lichens and mosses (8)", "#FF81FF"),
    ("Non- and sparsely-vegetated (9)", "#BFBFBF"),
    ("Water (10)", "#0080FF"),
]

image_url10 = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2021/4017000_2974190_0_402.tif"
)
label_url10 = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/labels/LU000/2021/4017000_2974190_0_402.npy"
)

with rasterio.open(image_url10) as src:
    rgb_data10 = src.read([4, 3, 2])
    bounds_3035_10 = src.bounds
    crs10 = src.crs

rgb_overlay10 = np.transpose(rgb_data10, (1, 2, 0)).astype(np.float32)
rgb_overlay10 = np.clip(rgb_overlay10 / np.percentile(rgb_overlay10, 98), 0, 1)

with urllib.request.urlopen(label_url10) as response:
    label10 = np.load(io.BytesIO(response.read()))

color_lut = np.zeros((11, 4), dtype=np.float32)
color_lut[0] = [0, 0, 0, 0]
for i, (_, hex_color) in enumerate(classes10, start=1):
    color_lut[i] = list(to_rgba(hex_color, alpha=0.7))
label_rgba10 = color_lut[label10]

west10, south10, east10, north10 = transform_bounds(crs10, "EPSG:4326", *bounds_3035_10)
center_lat10 = (south10 + north10) / 2
center_lon10 = (west10 + east10) / 2

m10 = folium.Map(location=[center_lat10, center_lon10], zoom_start=15)
folium.raster_layers.ImageOverlay(
    image=rgb_overlay10,
    bounds=[[south10, west10], [north10, east10]],
    name="Sentinel-2 RGB",
).add_to(m10)
folium.raster_layers.ImageOverlay(
    image=label_rgba10,
    bounds=[[south10, west10], [north10, east10]],
    name="CLC+ Label",
    opacity=0.8,
).add_to(m10)
folium.LayerControl().add_to(m10)
m10.save("exercise10_map.html")
m10

# %%
