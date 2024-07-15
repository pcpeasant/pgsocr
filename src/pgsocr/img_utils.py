import numpy as np
import numpy.typing as npt
from PIL import Image, ImageOps
import warnings
from .pgsparser import *
from typing import Generator


def read_rle_bytes(ods_bytes: bytes) -> list[int]:

    pixels = []
    line_builder = []

    i = 0
    while i < len(ods_bytes):
        if ods_bytes[i]:
            incr = 1
            color = ods_bytes[i]
            length = 1
        else:
            check = ods_bytes[i + 1]
            if check == 0:
                incr = 2
                color = 0
                length = 0
                pixels.append(line_builder)
                line_builder = []
            elif check < 64:
                incr = 2
                color = 0
                length = check
            elif check < 128:
                incr = 3
                color = 0
                length = ((check - 64) << 8) + ods_bytes[i + 2]
            elif check < 192:
                incr = 3
                color = ods_bytes[i + 2]
                length = check - 128
            else:
                incr = 4
                color = ods_bytes[i + 3]
                length = ((check - 192) << 8) + ods_bytes[i + 2]
        line_builder.extend([color] * length)
        i += incr

    if line_builder:
        warnings.warn(
            f"Improper image decode; hanging pixels: {line_builder}",
            RuntimeWarning,
            stacklevel=2,
        )

    return pixels


def ycbcr2rgb(ar: npt.NDArray) -> npt.NDArray[np.uint8]:
    xform = np.array([[1, 0, 1.402], [1, -0.34414, -0.71414], [1, 1.772, 0]])
    rgb = ar.astype(float)
    # Subtracting by 128 the R and G channels
    rgb[:, [1, 2]] -= 128
    # .dot is multiplication of the matrices and xform.T is a transpose of the array axes
    rgb = rgb.dot(xform.T)
    # Makes any pixel value greater than 255 just be 255 (Max for RGB colorspace)
    np.putmask(rgb, rgb > 255, 255)
    # Sets any pixel value less than 0 to 0 (Min for RGB colorspace)
    np.putmask(rgb, rgb < 0, 0)
    return np.uint8(rgb)  # type: ignore


def px_rgb_a(
    ods: ObjectDefinitionSegment,
    pds: PaletteDefinitionSegment,
    swap: bool,
) -> tuple[npt.NDArray[np.uint8], npt.NDArray[np.uint8], npt.NDArray[np.uint8]]:
    px = read_rle_bytes(ods.img_data)
    px = np.array([[255] * (ods.width - len(l)) + l for l in px], dtype=np.uint8)  # type: ignore

    if swap:
        ycbcr = np.array([(entry.Y, entry.Cb, entry.Cr) for entry in pds.palette])
    else:
        ycbcr = np.array([(entry.Y, entry.Cr, entry.Cb) for entry in pds.palette])

    rgb = ycbcr2rgb(ycbcr)

    a = [entry.Alpha for entry in pds.palette]
    a = np.array([[a[x] for x in l] for l in px], dtype=np.uint8)

    return px, rgb, a


def make_image(
    ods: ObjectDefinitionSegment, pds: PaletteDefinitionSegment, swap: bool = False
):
    px, rgb, a = px_rgb_a(ods, pds, swap)
    alpha = Image.fromarray(a, mode="L")
    img = Image.fromarray(px, mode="P")
    img.putpalette(rgb)
    img.putalpha(alpha)
    img = img.convert("RGBA")
    return img


def preprocess_image(im: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1000, 1000), (0, 0, 0))
    im_text = im.convert("RGB")
    # im_text = im_text.point(lambda p: 255 if p > 127 else 0)
    im_text.thumbnail((750, 750))
    bg_width, bg_height = canvas.size
    fg_width, fg_height = im_text.size
    position = ((bg_width - fg_width) // 2, (bg_height - fg_height) // 2)
    canvas.paste(im_text, position)
    canvas = ImageOps.invert(canvas)
    return canvas


def extract_images(pgsobj: PGStream) -> Generator[PGSImageObject, None, None]:
    seen_pcs = set()
    for e in pgsobj.epochs:
        ods_cache: dict[int, ObjectDefinitionSegment] = {}
        pds_cache: dict[int, PaletteDefinitionSegment] = {}

        screen: dict[ObjectDefinitionSegment, PGSImageObject] = {}
        for ds in e.display_sets:
            for pal in ds.pds:
                pds_cache[pal.id] = pal

            for obj in ds.ods:
                ods_cache[obj.id] = obj

            pcs = ds.pcs[0]
            cur_pts = pcs.presentation_timestamp
            pds_to_use = pds_cache[pcs.palette_id]

            ods_in_ds = set()
            if pcs.composition_number in seen_pcs:
                continue
            seen_pcs.add(pcs.composition_number)
            for comp in pcs.composition_objects:
                ods_to_use = ods_cache[comp.object_id]
                img = make_image(ods_to_use, pds_to_use)
                if comp.is_cropped:
                    crop_rect = (
                        comp.crop_x_offset,
                        comp.crop_y_offset,
                        comp.crop_x_offset + comp.crop_width,
                        comp.crop_y_offset + comp.crop_height,
                    )
                    img = img.crop(crop_rect)

                ods_in_ds.add(ods_to_use)
                screen[ods_to_use] = PGSImageObject(
                    img, comp.x_pos, comp.y_pos, cur_pts, -1, pds_to_use.palette
                )

            for k, v in screen.copy().items():
                if k not in ods_in_ds:
                    v.end_ms = cur_pts
                    yield v
                    del screen[k]
