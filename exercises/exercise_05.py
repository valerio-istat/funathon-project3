# %%
# Exercise 5 - Find and display the satellite tile for your city
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import requests
from shapely.geometry import Point

CITY = "Brussels, Belgium"
YEAR = 2024

geo_resp = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": CITY, "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
    timeout=30,
)
geo_resp.raise_for_status()
geo = geo_resp.json()
if not geo:
    raise RuntimeError(f"No geocoding result for {CITY}.")

lon, lat = float(geo[0]["lon"]), float(geo[0]["lat"])
city_point = gpd.GeoDataFrame(
    {"city": [CITY]}, geometry=[Point(lon, lat)], crs="EPSG:4326"
).to_crs("EPSG:3035")

nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)
city_nuts = gpd.sjoin(city_point, nuts, predicate="within")
if city_nuts.empty:
    raise RuntimeError("City point did not match any NUTS3 polygon.")

nuts_code = city_nuts.iloc[0]["NUTS_ID"]
parquet_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{YEAR}/filename2bbox.parquet"
)
tiles = pd.read_parquet(parquet_url)

x = city_point.geometry.iloc[0].x
y = city_point.geometry.iloc[0].y

tile_filename = None
for _, row in tiles.iterrows():
    xmin, ymin, xmax, ymax = row["bbox"]
    if xmin <= x <= xmax and ymin <= y <= ymax:
        tile_filename = row["filename"]
        break

if tile_filename is None:
    raise RuntimeError("No matching tile found for the city point.")

tile_url_city = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{YEAR}/{tile_filename}"
)
with rasterio.open(tile_url_city) as src:
    rgb_data_city = src.read([4, 3, 2])

rgb_city = np.transpose(rgb_data_city, (1, 2, 0)).astype(np.float32)
rgb_city = np.clip(rgb_city / np.percentile(rgb_city, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb_city)
ax.set_title(f"Sentinel-2 - {tile_filename}")
ax.axis("off")
plt.tight_layout()
plt.show()
