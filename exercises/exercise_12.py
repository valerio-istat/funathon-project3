# %%
# Exercise 12 (optional) - Save label as .npy and upload to S3
import os
import sys
from pathlib import Path

import numpy as np
import requests
from rasterio.io import MemoryFile

# Ensure local `src` package is importable even when running from `exercises/`.
PROJECT_ROOT12 = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT12) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT12))

year12 = 2021
bbox12 = [3649890, 2331750, 3652390, 2334250]
xmin, ymin, xmax, ymax = bbox12
resolution = 10
size_x = int((xmax - xmin) / resolution)
size_y = int((ymax - ymin) / resolution)

export_url12 = (
    f"https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/CLC_plus/"
    f"CLMS_CLCplus_RASTER_{year12}_010m_eu/ImageServer/exportImage"
)
params12 = {
    "f": "image",
    "bbox": f"{xmin},{ymin},{xmax},{ymax}",
    "bboxSR": "3035",
    "imageSR": "3035",
    "size": f"{size_x},{size_y}",
    "format": "tiff",
}
resp12 = requests.get(export_url12, params=params12, timeout=60)
resp12.raise_for_status()
with MemoryFile(resp12.content) as memfile:
    with memfile.open() as src:
        img_array12 = src.read(1)
img_array12[(img_array12 == 254) | (img_array12 == 255)] = 0

local_path12 = "3649890_2331750_0_937.npy"
np.save(local_path12, img_array12)
print(f"Saved local label file: {local_path12}")

if all(k in os.environ for k in ["AWS_S3_ENDPOINT", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]):
    try:
        from src.utils import get_file_system

        fs12 = get_file_system()
        s3_path12 = (
            "projet-funathon/2026/project3/data/labels/"
            "LU000/2021/3649890_2331750_0_937.npy"
        )
        fs12.put(local_path12, s3_path12)
        print(fs12.ls("projet-funathon/2026/project3/data/labels/LU000/2021"))
    except Exception as exc:
        print(f"Exercise 12 upload skipped due to S3 auth/runtime error: {exc}")
else:
    print("Exercise 12 upload skipped: missing AWS_* environment variables.")

# %%
