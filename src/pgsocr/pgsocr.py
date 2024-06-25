from tesserocr import PyTessBaseAPI
from pgsparser import PGStream
from utils import extract_images
import argparse
from pathlib import Path
import os


def generate_timecode(millis: int) -> str:
    seconds, milliseconds = divmod(millis, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def preprocess_image(im):
    return im.convert("RGB")


def sup2srt(in_path, out_path):
    if in_path.suffix != ".sup":
        print("File is not a SUP file, skipping")
        return
    supfile = PGStream(in_path)
    srtfile = open(f"{str(out_path)}/{in_path.stem}.srt", "a")
    print(f"Converting {supfile.file_name}...")
    with PyTessBaseAPI(path="/usr/share/tessdata", lang="eng") as api:
        api.SetVariable("debug_file", os.devnull)
        seq_num = 1
        for img, start, end in extract_images(supfile):
            api.SetImage(preprocess_image(img))
            srtfile.write(
                f"{seq_num}\n{generate_timecode(start)} --> {generate_timecode(end)}\n{api.GetUTF8Text()}\n\n"
            )
            seq_num += 1

    srtfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="pgsocr")
    parser.add_argument(
        "-i",
        help="Specify the path to the SUP file or (batch mode) directory.",
    )
    parser.add_argument("-o", help="Specify the path to the output directory.")
    args = parser.parse_args()

    inp = Path(args.i)

    if not inp.exists():
        print("File not found, make sure you have specified the correct path.")
        exit(1)

    if inp.is_file():
        sup2srt(inp, args.o)
    elif inp.is_dir():
        for x in inp.iterdir():
            sup2srt(x, args.o)
    exit(0)
