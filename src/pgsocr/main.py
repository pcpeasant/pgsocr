import argparse
from pathlib import Path
from .supconvert import sup2srt


def main():
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
        "-m",
        help="Specify the OCR model to use",
        choices=["tesseract", "florence2"],
        default="tesseract",
    )
    parser.add_argument("-l", help="Specify the languages to be used.", default="eng")
    parser.add_argument(
        "-b", help="Specify a custom character blacklist", default="|`´®"
    )
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

    langs = [s.strip() for s in args.l.split(",")]

    if args.m == "tesseract":
        from .tesseract_ocr_engine import TesseractOCREngine

        engine = TesseractOCREngine(langs, args.b)

    elif args.m == "florence2":
        from .transformer_ocr_engines import Florence2OCREngine

        engine = Florence2OCREngine()

    if inp.is_file():
        sup2srt(inp, args.o, engine)
    elif inp.is_dir():
        for x in inp.iterdir():
            sup2srt(x, args.o, engine)
    exit(0)
