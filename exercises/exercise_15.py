# ruff: noqa: E402
# %%
# Exercise 15 (optional) - Search and download Sentinel-2 product via OData
import os

import requests

odata_url15 = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
filter_parts15 = [
    "Collection/Name eq 'SENTINEL-2'",
    "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')",
    "ContentDate/Start gt 2021-06-01T00:00:00.000Z",
    "ContentDate/Start lt 2021-08-31T23:59:59.999Z",
    "Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt 15.00)",
    "OData.CSC.Intersects(area=geography'SRID=4326;POINT(6.1296 49.6341)')",
]
params15 = {
    "$filter": " and ".join(filter_parts15),
    "$top": 5,
    "$orderby": "ContentDate/Start desc",
}
resp15 = requests.get(odata_url15, params=params15, timeout=60)
resp15.raise_for_status()
products15 = resp15.json().get("value", [])
print(f"Exercise 15 products found: {len(products15)}")
for p in products15[:3]:
    print(f"{p['Name']} — {p['ContentDate']['Start'][:10]}")

cdse_user = os.environ.get("CDSE_USERNAME")
cdse_pass = os.environ.get("CDSE_PASSWORD")
if products15 and cdse_user and cdse_pass:
    token_url15 = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    try:
        token_resp15 = requests.post(
            token_url15,
            data={
                "grant_type": "password",
                "username": cdse_user,
                "password": cdse_pass,
                "client_id": "cdse-public",
            },
            timeout=60,
        )
        token_resp15.raise_for_status()
        access_token15 = token_resp15.json()["access_token"]
        product_id15 = products15[0]["Id"]
        download_url15 = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id15})/$value"
        dl15 = requests.get(
            download_url15,
            headers={"Authorization": f"Bearer {access_token15}"},
            stream=True,
            timeout=120,
        )
        dl15.raise_for_status()
        with open("product.zip", "wb") as f:
            for chunk in dl15.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Exercise 15 download complete: product.zip")
    except Exception as exc:
        print(f"Exercise 15 download skipped due to auth/runtime error: {exc}")
else:
    print("Exercise 15 download skipped: missing CDSE_USERNAME/CDSE_PASSWORD or no products.")
