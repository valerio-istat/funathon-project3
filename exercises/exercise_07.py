# %%
# Exercise 7 - Spatial join with NUTS3 regions
import geopandas as gpd
import rasterio
from shapely.geometry import box

TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)
NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)

with rasterio.open(TILE_URL) as src:
    tile_bounds = src.bounds
    tile_crs = src.crs

nuts = gpd.read_file(NUTS_URL)
tile_geom = box(*tile_bounds)
tile_gdf = gpd.GeoDataFrame({"tile": ["LU000"]}, geometry=[tile_geom], crs=tile_crs)
joined = gpd.sjoin(tile_gdf, nuts, predicate="intersects")

for _, row in joined.iterrows():
    print(f"NUTS_ID: {row['NUTS_ID']}, NUTS_NAME: {row['NUTS_NAME']}")

area_km2 = tile_geom.area / 1e6
print(f"Tile area: {area_km2:.2f} km^2")
# %%
