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


def sup2srt(in_path, out_path, tessdata_path, languages):
    if in_path.suffix != ".sup":
        print("File is not a SUP file, skipping")
        return
    supfile = PGStream(in_path)
    srtfile = open(f"{str(out_path)}/{in_path.stem}.srt", "a")
    tesspath = Path(tessdata_path)
    if not tesspath.exists() or not tesspath.is_dir():
        print("Invalid tessdata path specified.")
        exit(1)
    langfiles = list(map(lambda x: x.name, tesspath.glob("*.traineddata")))
    if not langfiles:
        print(
            "No language packs found, please make sure you have specified the correct tessdata path."
        )
        exit(1)
    for l in languages:
        if f"{l}.traineddata" not in langfiles:
            print(
                f"Failed to load language '{l}', make sure you have specified the correct language code"
                " and that the corresponding Tesseract language pack is installed on your system."
            )
            exit(1)
    langstring = "+".join(l for l in languages)
    print(f"Converting {supfile.file_name}...")
    with PyTessBaseAPI(path=tessdata_path, lang=langstring) as api:
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
        required=True,
    )
    parser.add_argument(
        "-o", help="Specify the path to the output directory.", required=True
    )
    parser.add_argument(
        "-t", help="Specify the path to the tessdata directory.", required=True
    )
    parser.add_argument("-l", help="Specify the languages to be used.")
    args = parser.parse_args()

    inp = Path(args.i)
    if not inp.exists():
        print("Input file not found, make sure you have specified the correct path.")
        exit(1)
    op = Path(args.o)
    if not op.exists() or not op.is_dir():
        print(
            "Output directory not found, make sure you have specified the correct path."
        )
        exit(1)

    if args.l:
        langs = [s.strip() for s in args.l.split(",")]
    else:
        print("No language specified, defaulting to English...")
        langs = ["eng"]

    if inp.is_file():
        sup2srt(inp, args.o, args.t, langs)
    elif inp.is_dir():
        for x in inp.iterdir():
            sup2srt(x, args.o, args.t, langs)
    exit(0)
