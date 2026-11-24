"""Join several captures of one scrolled week into a single tall image."""
from PIL import Image


def stitch_vertical(paths: list[str], dst: str) -> None:
    """Stack the images top-to-bottom (width = widest) and save to dst as PNG."""
    imgs = [Image.open(p) for p in paths]
    out = Image.new("RGB", (max(i.width for i in imgs), sum(i.height for i in imgs)))
    y = 0
    for i in imgs:
        out.paste(i.convert("RGB"), (0, y))
        y += i.height
    out.save(dst, "PNG")
