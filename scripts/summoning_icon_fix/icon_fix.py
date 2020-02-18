# This script fixes some unit icons, which have artifacts in their shadows. The shadows of all known-bad icons are
# replaced with the shadow from a known-good icon. The script assumes it is placed in the /scripts/summoning_icon_fix
# directory of the main project.

import pathlib
import json
from PIL import Image

with open("config.json") as fp:
    config = json.load(fp)
    good_icon_name = config["known_good_icon"]
    bad_icon_names = config["known_bad_icons"]

base_path = pathlib.Path("../../data/icons").resolve()
shadow_base = Image.open(base_path / good_icon_name)
shadow_mask = Image.open("mask.png")

for icon_name in bad_icon_names:
    try:
        icon: Image.Image = Image.open(base_path / icon_name)
    except FileNotFoundError:
        print(f"No such file {icon_name}")
        continue
    icon.paste(shadow_base, mask=shadow_mask)
    icon.save(base_path / icon_name, compress_level=1)
    print(f"Saved {icon_name}")
