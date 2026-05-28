# %%
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    rgb_data = src.read([4, 3, 2])
    tile_crs = src.crs
    tile_bounds = src.bounds

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    print(src.profile)
    fc_data = src.read([8, 4, 3])

fc = np.transpose(fc_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(fc, 98)
fc = np.clip(fc / p98, 0, 1)

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
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    # Healthy vegetation strongly reflects near-infrared (B8) and absorbs red (B4),
    # so the ratio (NIR − Red) / (NIR + Red) gives a clean vegetation signal.
    nir = src.read(8).astype(np.float32)
    red = src.read(4).astype(np.float32)

# np.where guards against pixels where NIR + Red is exactly 0 (water bodies,
# nodata, deep shadow): the ratio would otherwise produce NaN and contaminate the
# colormap. Substituting 0 keeps those pixels neutral on the red-yellow-green scale.
ndvi = np.where(nir + red == 0, 0, (nir - red) / (nir + red))

fig, ax = plt.subplots(figsize=(6, 5))
# vmin=-1, vmax=1 anchors the colormap to NDVI's full theoretical range, so the
# same colour means the same vegetation cover across tiles.
im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
ax.set_title("NDVI — LU000 (2024)")
ax.axis("off")
fig.colorbar(im, ax=ax, shrink=0.8, label="NDVI")
plt.tight_layout()
plt.show()

# %%
import requests
import geopandas as gpd
from shapely.geometry import Point

# Step 1: Geocode Brussels
response = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Brussels, Belgium", "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
)
result = response.json()[0]
lon, lat = float(result["lon"]), float(result["lat"])
print(f"Brussels coordinates: lon={lon}, lat={lat}")

# Step 2: Create GeoDataFrame and reproject
city_point = gpd.GeoDataFrame(
    {"city": ["Brussels"]}, geometry=[Point(lon, lat)], crs="EPSG:4326"
)
city_point = city_point.to_crs("EPSG:3035")

# Step 3: Load NUTS3 boundaries and spatial join
nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)
city_nuts = gpd.sjoin(city_point, nuts, predicate="within")
nuts_code = city_nuts.iloc[0]["NUTS_ID"]
print(f"NUTS3 region: {nuts_code}")  # → BE100

# Step 4: Check availability
available = [
    "AT332",
    "BE100",
    "BE251",
    "BG322",
    "CY000",
    "CZ072",
    "DEA54",
    "DK041",
    "EE00A",
    "EL521",
    "ES612",
    "FI1C1",
    "FRJ27",
    "FRK26",
    "HR050",
    "IE061",
    "ITI32",
    "LT028",
    "LU000",
    "LV008",
    "MT001",
    "NL33C",
    "PL414",
    "PT16I",
    "RO123",
    "SE311",
    "SI035",
    "SK022",
    "UKJ22",
]
print(f"Available: {nuts_code in available}")  # → True

# Step 5: Build S3 URL
base_url = f"s3://projet-funathon/2026/project3/data/images/{nuts_code}"  # TODO
print(base_url)

# %%
import pandas as pd
import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Step 1: Build the parquet URL
year = 2024
parquet_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/filename2bbox.parquet"
)

# Step 2: Read the tile index
tiles = pd.read_parquet(parquet_url)
print(f"{len(tiles)} tiles available")

# Step 3: Get city coordinates in EPSG:3035
x = city_point.geometry.iloc[0].x
y = city_point.geometry.iloc[0].y

# Step 4: Find the matching tile
tile_filename = None
for _, row in tiles.iterrows():
    xmin, ymin, xmax, ymax = row["bbox"]
    if xmin <= x <= xmax and ymin <= y <= ymax:
        tile_filename = row["filename"]
        break

print(f"Matching tile: {tile_filename}")

# Step 5: Build the full tile URL
tile_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/{tile_filename}"
)

# Step 6: Open, read RGB, normalize and display
with rasterio.open(tile_url) as src:
    rgb_data = src.read([4, 3, 2])
    tile_crs = src.crs
    tile_bounds = src.bounds

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title(f"Sentinel-2 — {tile_filename}")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
import geopandas as gpd
from shapely.geometry import box

tile_geom = box(*tile_bounds)
gdf = gpd.GeoDataFrame({"tile": ["LU000"]}, geometry=[tile_geom], crs="EPSG:3035")
gdf_wgs84 = gdf.to_crs("EPSG:4326")

print("EPSG:3035 bounds:", gdf.total_bounds)
print("EPSG:4326 bounds:", gdf_wgs84.total_bounds)

import geopandas as gpd
from shapely.geometry import box

nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)

tile_geom = box(*tile_bounds)
tile_gdf = gpd.GeoDataFrame(
    {"tile": ["LU000"]}, geometry=[tile_geom], crs=tile_crs
)

# Spatial join: for each tile geometry, attach the columns of every NUTS3 region
# whose geometry satisfies the predicate. `predicate="intersects"` keeps any region
# that touches the tile (even partially); alternatives are "within" (tile fully
# inside region) or "contains" (region fully inside tile). A tile straddling a
# border can therefore match several NUTS3 regions — hence the loop below.
joined = gpd.sjoin(tile_gdf, nuts, predicate="intersects")

for _, row in joined.iterrows():
    print(f"NUTS_ID: {row['NUTS_ID']}, NUTS_NAME: {row['NUTS_NAME']}")

# tile_geom is in EPSG:3035 whose unit is the metre, so .area is in m². Divide by
# 1e6 to get km². Computing area on a geographic CRS like EPSG:4326 (degrees) would
# give a meaningless figure — always use a metric projection for measurements.
area_km2 = tile_geom.area / 1e6
print(f"Tile area: {area_km2:.2f} km²")

# %%
import folium
import numpy as np
from folium.raster_layers import ImageOverlay
from rasterio.transform import from_bounds
from rasterio.warp import (
    transform_bounds,
    reproject,
    Resampling,
    calculate_default_transform,
)
from rasterio.crs import CRS

dst_crs = CRS.from_epsg(4326)

# Step 1: Compute the WGS84 output grid that covers the tile
h, w = rgb_data.shape[1], rgb_data.shape[2]
src_transform = from_bounds(*tile_bounds, w, h)
dst_transform, dst_w, dst_h = calculate_default_transform(
    tile_crs, dst_crs, w, h, *tile_bounds
)

# Step 2: Reproject each RGB band onto that grid
rgb_wgs84_bands = np.zeros((3, dst_h, dst_w), dtype=np.float32)
for i in range(3):
    reproject(
        source=rgb_data[i].astype(np.float32),
        destination=rgb_wgs84_bands[i],
        src_transform=src_transform,
        src_crs=tile_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
    )

# Step 3: Normalize to [0, 1] and build the alpha channel
p98 = np.percentile(rgb_wgs84_bands[rgb_wgs84_bands > 0], 98)
rgb_wgs84 = np.clip(np.transpose(rgb_wgs84_bands, (1, 2, 0)) / p98, 0, 1)
alpha = (rgb_wgs84_bands.max(axis=0) > 0).astype(np.float32)
rgba_wgs84 = np.dstack([rgb_wgs84, alpha])

# Step 4: Reproject the bounds and centre the map
west, south, east, north = transform_bounds(tile_crs, dst_crs, *tile_bounds)
center_lat = (south + north) / 2
center_lon = (west + east) / 2

# Step 5: Build the map
m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
ImageOverlay(
    image=rgba_wgs84,
    bounds=[[south, west], [north, east]],
    opacity=0.7,
).add_to(m)

# %%
import urllib.request
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

nuts_code = "LU000"
year = 2021
patch_id = "4042000_2951690_0_637"

label_url = f"https://minio.lab.sspcloud.fr/projet-funathon/2026/project3/data/labels/{nuts_code}/{year}/{patch_id}.npy"

with urllib.request.urlopen(label_url) as response:
    my_label = np.load(io.BytesIO(response.read()))

print(f"Shape: {my_label.shape}")
print(f"Classes: {np.unique(my_label)}")

cmap = ListedColormap(
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
ax.imshow(my_label, cmap=cmap, vmin=1, vmax=10)
ax.set_title(f"CLC+ label — {nuts_code}/{year}/{patch_id}")
ax.axis("off")
plt.show()

# %%
import numpy as np
import urllib.request
import io
import rasterio
import folium
from rasterio.transform import from_bounds
from rasterio.warp import (
    transform_bounds,
    reproject,
    Resampling,
    calculate_default_transform,
)
from rasterio.crs import CRS
from matplotlib.colors import to_rgba

classes = [
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

# Step 1: Load satellite image
image_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2021/4017000_2974190_0_402.tif"
)
with rasterio.open(image_url) as src:
    rgb_data = src.read([4, 3, 2])
    bounds_3035 = src.bounds
    crs = src.crs

# Step 2: Load the matching label
label_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/labels/LU000/"
    "2021/4017000_2974190_0_402.npy"
)
with urllib.request.urlopen(label_url) as response:
    label = np.load(io.BytesIO(response.read()))

# Step 3: Reproject both rasters onto a common WGS84 grid.
# RGB → Resampling.bilinear (continuous values); label → Resampling.nearest
# (categorical: averaging integer class IDs would invent classes that don't exist).
dst_crs = CRS.from_epsg(4326)
h, w = rgb_data.shape[1], rgb_data.shape[2]
src_transform = from_bounds(*bounds_3035, w, h)
dst_transform, dst_w, dst_h = calculate_default_transform(
    crs, dst_crs, w, h, *bounds_3035
)

rgb_wgs84_bands = np.zeros((3, dst_h, dst_w), dtype=np.float32)
for i in range(3):
    reproject(
        source=rgb_data[i].astype(np.float32),
        destination=rgb_wgs84_bands[i],
        src_transform=src_transform,
        src_crs=crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
    )

label_wgs84 = np.zeros((dst_h, dst_w), dtype=label.dtype)
reproject(
    source=label,
    destination=label_wgs84,
    src_transform=src_transform,
    src_crs=crs,
    dst_transform=dst_transform,
    dst_crs=dst_crs,
    resampling=Resampling.nearest,
)

# Step 4: Build RGB overlay (normalize + alpha for empty corners) and label RGBA.
p98 = np.percentile(rgb_wgs84_bands[rgb_wgs84_bands > 0], 98)
rgb_overlay = np.clip(np.transpose(rgb_wgs84_bands, (1, 2, 0)) / p98, 0, 1)
alpha = (rgb_wgs84_bands.max(axis=0) > 0).astype(np.float32)
rgba_overlay = np.dstack([rgb_overlay, alpha])

color_lut = np.zeros((11, 4), dtype=np.float32)
color_lut[0] = [0, 0, 0, 0]
for i, (_, hex_color) in enumerate(classes, start=1):
    color_lut[i] = list(to_rgba(hex_color, alpha=0.7))

label_rgba = color_lut[label_wgs84]

# Step 5: Reproject bounds and build the map
west, south, east, north = transform_bounds(crs, "EPSG:4326", *bounds_3035)

center_lat = (south + north) / 2
center_lon = (west + east) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

folium.raster_layers.ImageOverlay(
    image=rgba_overlay,
    bounds=[[south, west], [north, east]],
    name="Sentinel-2 RGB",
).add_to(m)

folium.raster_layers.ImageOverlay(
    image=label_rgba,
    bounds=[[south, west], [north, east]],
    name="CLC+ Label",
    opacity=0.8,
).add_to(m)

# Step 6: Layer control
folium.LayerControl().add_to(m)

# %%
from src.models.model import SegformerB5

# This downloads ~330 MB of weights from HuggingFace on first run
model = SegformerB5(
    # 14 matches the layout of the pre-baked GeoTIFFs: the 12 L2A spectral bands
    # (B10 is dropped by atmospheric correction) plus NDVI and NDWI as derived
    # channels. `src/download_region.py` produces the same layout. If you swap in
    # a different dataset (different band count or different derived layers), this
    # number, the normalisation statistics, and `num_channels` in the SegformerConfig
    # must all change together — otherwise the first patch-embedding layer
    # mis-shapes inputs.
    n_bands=14,
    logits=True,             # return raw logits (not probabilities)
    freeze_encoder=False,    # keep encoder trainable
    type_labeler="CLCplus-Backbone",
)
# %%
