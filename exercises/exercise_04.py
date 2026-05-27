# %%
# Exercise 4 - Geocode a city and build a tile URL
import geopandas as gpd
import requests
from shapely.geometry import Point

response = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Brussels, Belgium", "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
    timeout=30,
)
response.raise_for_status()
geo = response.json()
if not geo:
    raise RuntimeError("Nominatim did not return any result for the city query.")

lon, lat = float(geo[0]["lon"]), float(geo[0]["lat"])
city_point = gpd.GeoDataFrame(
    {"city": ["Brussels"]}, geometry=[Point(lon, lat)], crs="EPSG:4326"
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
base_url = f"s3://projet-funathon/2026/project3/data/images/{nuts_code}"
print(f"NUTS3: {nuts_code}")
print(base_url)

# %%
