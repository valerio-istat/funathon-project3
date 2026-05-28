# %%
# Exercise 9 - Load a CLC+ label from S3 and overlay it on a Folium map
import io
from pathlib import Path
import urllib.request

import folium
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import rasterio
from rasterio.warp import transform_bounds

nuts_code_9 = "ITI32"
year_9 = 2021
patch_id_9 = "4570210_2293160_0_73"
label_url_9 = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/labels/{nuts_code_9}/{year_9}/{patch_id_9}.npy"
)
image_url_9 = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code_9}/{year_9}/{patch_id_9}.tif"
)
with urllib.request.urlopen(label_url_9) as response:
    my_label = np.load(io.BytesIO(response.read()))

print(f"Shape: {my_label.shape}")
print(f"Classes: {np.unique(my_label)}")

cmap9 = ListedColormap(
    [
        "#FF0100",
        "#238B23",
        "#80FF00",
        "#00FF00",
        "#804000",
        "#CCF24E",
        "#FEFF80",
        "#FF81FF",
        "#BFBFBF",
        "#0080FF",
    ]
)
fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(my_label, cmap=cmap9, vmin=1, vmax=10)
ax.set_title(f"CLC+ label - {nuts_code_9}/{year_9}/{patch_id_9}")
ax.axis("off")
plt.show()

# Convert label IDs into an RGBA image for Folium overlay.
normalized = np.clip((my_label - 1) / 9, 0, 1)
rgba_overlay = (cmap9(normalized) * 255).astype(np.uint8)
rgba_overlay[..., 3] = np.where(my_label > 0, 180, 0).astype(np.uint8)

with rasterio.open(image_url_9) as src:
    left, bottom, right, top = src.bounds
    west, south, east, north = transform_bounds(
        src.crs, "EPSG:4326", left, bottom, right, top
    )

bounds = [[south, west], [north, east]]
center = [(south + north) / 2, (west + east) / 2]

folium_map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")
folium.raster_layers.ImageOverlay(
    image=rgba_overlay,
    bounds=bounds,
    origin="upper",
    opacity=0.7,
    name="CLC+ labels",
).add_to(folium_map)
folium.LayerControl().add_to(folium_map)

output_html = (
    Path(__file__).resolve().parent
    / f"exercise_09_map_{nuts_code_9}_{year_9}_{patch_id_9}.html"
)
folium_map.save(output_html)
print(f"Saved folium map: {output_html}")

# %%
