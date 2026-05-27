# %%
# Exercise 5 - Find and display the satellite tile for your city
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import requests
from shapely.geometry import Point, box

CITY_OPTIONS = {
    "brussels": "Brussels, Belgium",
    "luxembourg": "Luxembourg City, Luxembourg",
}
# Available choices: "brussels", "luxembourg"
CITY_CHOICE = "luxembourg"
if CITY_CHOICE not in CITY_OPTIONS:
    available = ", ".join(sorted(CITY_OPTIONS))
    raise ValueError(f"Unknown CITY_CHOICE {CITY_CHOICE!r}. Choose one of: {available}")

CITY = CITY_OPTIONS[CITY_CHOICE]
YEAR = 2024
TARGET_CRS = "EPSG:3035"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)


def geocode_city(city: str) -> dict:
    response = requests.get(
        NOMINATIM_URL,
        params={"q": city, "format": "json", "limit": 1},
        headers={"User-Agent": "funathon-project3"},
        timeout=30,
    )
    response.raise_for_status()
    matches = response.json()
    if not matches:
        raise RuntimeError(f"No geocoding result for {city!r}.")
    return matches[0]


def city_point_in_3035(city: str) -> gpd.GeoDataFrame:
    match = geocode_city(city)
    lon = float(match["lon"])
    lat = float(match["lat"])
    return gpd.GeoDataFrame(
        {"city": [city], "display_name": [match.get("display_name", city)]},
        geometry=[Point(lon, lat)],
        crs="EPSG:4326",
    ).to_crs(TARGET_CRS)


def nuts3_for_point(point_gdf: gpd.GeoDataFrame) -> str:
    nuts = gpd.read_file(NUTS_URL)
    joined = gpd.sjoin(point_gdf, nuts, predicate="within")
    if joined.empty:
        raise RuntimeError(f"{CITY!r} did not match a NUTS3 region.")
    return joined.iloc[0]["NUTS_ID"]


def tile_index(nuts_code: str, year: int) -> gpd.GeoDataFrame:
    parquet_url = (
        f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
        f"project3/data/images/{nuts_code}/{year}/filename2bbox.parquet"
    )
    tiles = pd.read_parquet(parquet_url)
    geometries = [box(*bbox) for bbox in tiles["bbox"]]
    return gpd.GeoDataFrame(tiles, geometry=geometries, crs=TARGET_CRS)


def find_covering_tile(tiles: gpd.GeoDataFrame, point: Point) -> str:
    matches = tiles[tiles.geometry.covers(point)].sort_values("filename")
    if matches.empty:
        raise RuntimeError(f"No tile found for {CITY!r}.")
    if len(matches) > 1:
        print(f"Found {len(matches)} matching tiles; using the first by filename.")
    return matches.iloc[0]["filename"]


def rgb_for_display(tile_url: str) -> np.ndarray:
    with rasterio.open(tile_url) as src:
        rgb_data = src.read([4, 3, 2])
    rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
    return np.clip(rgb / np.percentile(rgb, 98), 0, 1)


city_point = city_point_in_3035(CITY)
nuts_code = nuts3_for_point(city_point)
tiles = tile_index(nuts_code, YEAR)
tile_filename = find_covering_tile(tiles, city_point.geometry.iloc[0])
tile_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{YEAR}/{tile_filename}"
)

print(f"City: {CITY}")
print(f"NUTS3: {nuts_code}")
print(f"Tile: {tile_filename}")
print(tile_url)

rgb = rgb_for_display(tile_url)

fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(rgb)
ax.set_title(f"Sentinel-2 RGB - {CITY}")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
