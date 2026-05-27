# %%
# Exercise 14 (optional) - Save downloaded tile and upload to S3
import os

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

city14 = "Paris, France"
geo_resp14 = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": city14, "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
    timeout=30,
)
geo_resp14.raise_for_status()
geo14 = geo_resp14.json()
if not geo14:
    raise RuntimeError("Exercise 14 failed: city geocoding returned no result.")

lon14, lat14 = float(geo14[0]["lon"]), float(geo14[0]["lat"])
delta14 = 0.05
bbox14 = [lon14 - delta14, lat14 - delta14, lon14 + delta14, lat14 + delta14]

response14 = None
client_id14 = os.environ.get("CDSE_CLIENT_ID")
client_secret14 = os.environ.get("CDSE_CLIENT_SECRET")
if client_id14 and client_secret14:
    client14 = BackendApplicationClient(client_id=client_id14)
    oauth14 = OAuth2Session(client=client14)
    oauth14.fetch_token(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_secret=client_secret14,
        include_client_id=True,
    )
    process_url14 = "https://sh.dataspace.copernicus.eu/api/v1/process"
    evalscript14 = """
//VERSION=3
function setup() {
  return { input: ["B04", "B03", "B02"], output: { bands: 3, sampleType: "AUTO" } };
}
function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
"""
    body14 = {
        "input": {
            "bounds": {
                "bbox": bbox14,
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
        "evalscript": evalscript14,
    }
    response14 = oauth14.post(process_url14, json=body14)
    response14.raise_for_status()

if response14 is not None:
    local_path14 = "paris_rgb.tif"
    with open(local_path14, "wb") as f:
        f.write(response14.content)
    print(f"Saved {local_path14}")

    if all(k in os.environ for k in ["AWS_S3_ENDPOINT", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]):
        try:
            from src.utils import get_file_system

            fs14 = get_file_system()
            s3_path14 = "my-bucket/sentinel2/paris_rgb.tif"
            fs14.put(local_path14, s3_path14)
            print("Exercise 14 upload done.")
        except Exception as exc:
            print(f"Exercise 14 upload skipped due to S3 auth/runtime error: {exc}")
    else:
        print("Exercise 14 upload skipped: missing AWS_* environment variables.")
else:
    print("Exercise 14 skipped: set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET to execute.")

# %%
