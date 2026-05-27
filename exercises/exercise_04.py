# %%
# Exercise 4 - Geocode a city and build a tile URL
import geopandas as gpd
import requests
from shapely.geometry import Point

CITY = "Brussels, Belgium"
TARGET_CRS = "EPSG:3035"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
AVAILABLE_NUTS3 = {
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
}


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
        raise RuntimeError(f"Nominatim did not return any result for {city!r}.")
    match = matches[0]
    if "lon" not in match or "lat" not in match:
        raise RuntimeError(f"Nominatim result for {city!r} has no lon/lat fields.")
    return match


def city_point_3035(geocode_result: dict) -> gpd.GeoDataFrame:
    lon = float(geocode_result["lon"])
    lat = float(geocode_result["lat"])
    return gpd.GeoDataFrame(
        {"city": [CITY], "display_name": [geocode_result.get("display_name", CITY)]},
        geometry=[Point(lon, lat)],
        crs="EPSG:4326",
    ).to_crs(TARGET_CRS)


def find_containing_nuts3(point_gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    nuts = gpd.read_file(NUTS_URL)
    matched = gpd.sjoin(point_gdf, nuts, predicate="within")
    if matched.empty:
        raise RuntimeError(
            f"{CITY!r} did not fall within any NUTS3 polygon in {TARGET_CRS}."
        )
    return matched.iloc[0]


def build_image_base_url(nuts_code: str) -> str:
    return f"s3://projet-funathon/2026/project3/data/images/{nuts_code}"


geocode_result = geocode_city(CITY)
city_point = city_point_3035(geocode_result)
nuts_match = find_containing_nuts3(city_point)

nuts_code = nuts_match["NUTS_ID"]
base_url = build_image_base_url(nuts_code)
lon = float(geocode_result["lon"])
lat = float(geocode_result["lat"])

print(f"Resolved city: {geocode_result.get('display_name', CITY)}")
print(f"Coordinates: lon={lon:.5f}, lat={lat:.5f}")
print(f"Projected point ({TARGET_CRS}): {city_point.geometry.iloc[0]}")
print(f"NUTS3: {nuts_code} - {nuts_match['NUTS_NAME']}")
print(f"Available in tutorial dataset: {nuts_code in AVAILABLE_NUTS3}")
print(base_url)

# %%
