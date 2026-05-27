# %%
# Exercise 13 (optional) - Geocode a city and download Sentinel-2 via Processing API
import os

import matplotlib.pyplot as plt
import numpy as np
import requests
from oauthlib.oauth2 import BackendApplicationClient
from rasterio.io import MemoryFile
from requests_oauthlib import OAuth2Session

city13 = "Paris, France"
geo_resp13 = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": city13, "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
    timeout=30,
)
geo_resp13.raise_for_status()
geo13 = geo_resp13.json()
if not geo13:
    raise RuntimeError("Exercise 13 failed: city geocoding returned no result.")
lon13, lat13 = float(geo13[0]["lon"]), float(geo13[0]["lat"])
delta13 = 0.05
bbox13 = [lon13 - delta13, lat13 - delta13, lon13 + delta13, lat13 + delta13]

client_id13 = os.environ.get("CDSE_CLIENT_ID")
client_secret13 = os.environ.get("CDSE_CLIENT_SECRET")
response13 = None
if client_id13 and client_secret13:
    client13 = BackendApplicationClient(client_id=client_id13)
    oauth13 = OAuth2Session(client=client13)
    oauth13.fetch_token(
        token_url=(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/"
            "openid-connect/token"
        ),
        client_secret=client_secret13,
        include_client_id=True,
    )
    process_url13 = "https://sh.dataspace.copernicus.eu/api/v1/process"
    evalscript13 = """
//VERSION=3
function setup() {
  return { input: ["B04", "B03", "B02"], output: { bands: 3, sampleType: "AUTO" } };
}
function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
"""
    body13 = {
        "input": {
            "bounds": {
                "bbox": bbox13,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": "2024-06-01T00:00:00Z",
                            "to": "2024-08-31T23:59:59Z",
                        },
                        "maxCloudCoverage": 20,
                    },
                }
            ],
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
        },
        "evalscript": evalscript13,
    }
    response13 = oauth13.post(process_url13, json=body13)
    response13.raise_for_status()
    with MemoryFile(response13.content) as memfile:
        with memfile.open() as src:
            rgb13_data = src.read([1, 2, 3])
    rgb13 = np.transpose(rgb13_data, (1, 2, 0)).astype(np.float32)
    rgb13 = np.clip(rgb13 / np.percentile(rgb13, 98), 0, 1)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(rgb13)
    ax.set_title(f"Sentinel-2 true colour - {city13}")
    ax.axis("off")
    plt.tight_layout()
    plt.show()
else:
    print("Exercise 13 skipped: set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET to execute.")

# %%
