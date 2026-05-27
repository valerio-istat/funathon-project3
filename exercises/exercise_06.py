# %%
# Exercise 6 - Build a GeoDataFrame from tile bounds and convert CRS
import geopandas as gpd
import rasterio
from shapely.geometry import box

TILE_CODE = "LU000"
TILE_URL = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/2024/4034500_3011690_0_34.tif"
)

with rasterio.open(TILE_URL) as src:
    tile_bounds = src.bounds
    tile_crs = src.crs

tile_geom = box(*tile_bounds)
gdf = gpd.GeoDataFrame({"tile": [TILE_CODE]}, geometry=[tile_geom], crs=tile_crs)
gdf_wgs84 = gdf.to_crs("EPSG:4326")

print("EPSG:3035 bounds:", gdf.total_bounds)
print("EPSG:4326 bounds:", gdf_wgs84.total_bounds)

# %%
