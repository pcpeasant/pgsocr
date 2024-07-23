import argparse
from pathlib import Path
from .supconvert import sup2srt, sup2ass


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
    parser.add_argument(
        "-f",
        help="Specify the output format",
        choices=["srt", "ass"],
        default="srt",
    )
    parser.add_argument(
        "-l",
        nargs='+',
        help="Specify the languages to be used.",
        default=["eng"]
    )
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

    langs = args.l

    print("Loading OCR engine...")
    if args.m == "tesseract":
        from .tesseract_ocr_engine import TesseractOCREngine

        engine = TesseractOCREngine(langs, args.b)
    elif args.m == "florence2":
        from .transformer_ocr_engines import Florence2OCREngine

        engine = Florence2OCREngine()
    else:
        raise ValueError(f"Unknown OCR engine '{args.m}' specified.")
    print("OCR engine loaded.")

    if args.f == "srt":
        convertor = sup2srt
    elif args.f == "ass":
        convertor = sup2ass
    else:
        raise ValueError(f"Unknown output format '{args.f}' specified.")

    if inp.is_file():
        convertor(str(inp), args.o, engine)
    elif inp.is_dir():
        for x in inp.iterdir():
            convertor(str(x), args.o, engine)
    exit(0)
