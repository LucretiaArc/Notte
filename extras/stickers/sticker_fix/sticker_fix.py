# Fixes stickers with white borders. Mild artifacting can result, but output is visually indistinguishable from perfect.

from PIL import Image, ImageMath, UnidentifiedImageError
from pathlib import Path

working_path = Path(__file__).parent

mask: Image.Image = Image.open(working_path / "mask.png")
mask_bands = mask.split()

for path in (working_path / "input").iterdir():
    try:
        im: Image.Image = Image.open(path).convert("RGB")
    except UnidentifiedImageError:
        print(f"{path} not an image")
        continue

    im_bands = im.split()
    out_bands = []
    for band_a, band_b in list(zip(im_bands, mask_bands))[:3]:
        out_bands.append(ImageMath.eval("convert((a - b) * 255/(255 - b), 'L')", a=band_a, b=band_b))

    Image.merge("RGB", out_bands[:3]).save(working_path / "output" / path.name)
    print(f"processed {path.name}")