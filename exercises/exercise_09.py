# %%
# Exercise 9 - Load a CLC+ label from S3
import io
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

nuts_code_9 = "LU000"
year_9 = 2021
patch_id_9 = "4042000_2951690_0_637"
label_url_9 = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/labels/{nuts_code_9}/{year_9}/{patch_id_9}.npy"
)
with urllib.request.urlopen(label_url_9) as response:
    my_label = np.load(io.BytesIO(response.read()))

print(f"Shape: {my_label.shape}")
print(f"Classes: {np.unique(my_label)}")

cmap9 = ListedColormap(
    [
        "#FF0100",
        "#238B23",
        "#80FF00",
        "#00FF00",
        "#804000",
        "#CCF24E",
        "#FEFF80",
        "#FF81FF",
        "#BFBFBF",
        "#0080FF",
    ]
)
fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(my_label, cmap=cmap9, vmin=1, vmax=10)
ax.set_title(f"CLC+ label - {nuts_code_9}/{year_9}/{patch_id_9}")
ax.axis("off")
plt.show()

# %%
