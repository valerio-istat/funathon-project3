# %%
import geopandas as gpd
from shapely.geometry import box

# Create a GeoDataFrame with the tile extent in EPSG:3035
tile_geom = box(*tile_bounds)
gdf = gpd.GeoDataFrame({"tile": ["LU000"]}, geometry=[tile_geom], crs="EPSG:3035")

print("EPSG:3035 bounds:")
print(gdf.total_bounds)

# Convert to WGS84 (latitude/longitude)
gdf_wgs84 = gdf.to_crs("EPSG:4326")
print("\nEPSG:4326 bounds:")
print(gdf_wgs84.total_bounds)