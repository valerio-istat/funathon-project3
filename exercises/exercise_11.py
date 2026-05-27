# %%
# Exercise 11 (optional) - Download CLC+ label from ImageServer API
import numpy as np
import requests
from rasterio.io import MemoryFile

year11 = 2021
bbox11 = [3649890, 2331750, 3652390, 2334250]
xmin, ymin, xmax, ymax = bbox11
resolution = 10
size_x = int((xmax - xmin) / resolution)
size_y = int((ymax - ymin) / resolution)
export_url11 = (
    f"https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/CLC_plus/"
    f"CLMS_CLCplus_RASTER_{year11}_010m_eu/ImageServer/exportImage"
)
params11 = {
    "f": "image",
    "bbox": f"{xmin},{ymin},{xmax},{ymax}",
    "bboxSR": "3035",
    "imageSR": "3035",
    "size": f"{size_x},{size_y}",
    "format": "tiff",
}
resp11 = requests.get(export_url11, params=params11, timeout=60)
resp11.raise_for_status()
with MemoryFile(resp11.content) as memfile:
    with memfile.open() as src:
        img_array11 = src.read(1)
img_array11[(img_array11 == 254) | (img_array11 == 255)] = 0
print("Exercise 11:", img_array11.shape, img_array11.dtype, np.unique(img_array11)[:10])

# %%
