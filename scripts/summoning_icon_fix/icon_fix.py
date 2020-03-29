# This script fixes some unit icons, which have artifacts in their shadows resulting from alpha channel errors.
# The shadows of all bad icons are replaced with the shadow from a known-good icon, and their alpha channels are fixed.
# The script assumes it is placed in the /scripts/summoning_icon_fix directory of the main project.

import pathlib
from PIL import Image

base_path = pathlib.Path("../../data/icons")
shadow_base: Image.Image = Image.open("shadow_base.png")  # shadow image to use
shadow_mask: Image.Image = Image.open("shadow_mask.png")  # masks shadow replacement
alpha_histogram_reference = [5169] + [0]*127 + [831] + [0]*126 + [19600]  # histogram of correct alpha channel

for icon_path in base_path.iterdir():
    if icon_path.name[0] == "1":
        icon: Image.Image = Image.open(icon_path)
        icon_bands = icon.split()

        if icon_bands[3].histogram() != alpha_histogram_reference:
            new_icon = Image.merge("RGB", icon_bands[:3]).convert("RGBA")
            new_icon.paste(shadow_base, mask=shadow_mask)
            new_icon.save(icon_path, compress_level=1)
            print(f"Wrote {icon_path.name}")
