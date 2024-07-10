import argparse
from pathlib import Path
import ocr_engines
from supconvert import sup2srt

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
        "-m",
        help="Specify the OCR model to use",
        choices=["tesseract", "phi3v"],
        default="tesseract",
    )
    parser.add_argument("-l", help="Specify the languages to be used.", default="eng")
    parser.add_argument(
        "-b", help="Specify a custom character blacklist", default="|`´‘’“”®"
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
        engine = ocr_engines.TesseractOCREngine(langs, args.b)
    elif args.m == "phi3v":
        engine = ocr_engines.Phi3OCREngine2()

    if inp.is_file():
        sup2srt(inp, args.o, engine)
    elif inp.is_dir():
        for x in inp.iterdir():
            sup2srt(x, args.o, engine)
    exit(0)
