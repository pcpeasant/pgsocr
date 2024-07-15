from pathlib import Path
import os
from PIL import Image

from tesserocr import PyTessBaseAPI


class TesseractOCREngine:
    def __init__(self, languages, blacklist):
        if "TESSDATA_PREFIX" not in os.environ:
            print("Please set the TESSDATA_PREFIX environment variable first.")
            exit(1)
        tesspath = Path(os.environ["TESSDATA_PREFIX"])
        if not tesspath.exists() or not tesspath.is_dir():
            print(
                "Invalid tessdata path specified, make sure you have set the TESSDATA_PREFIX environment variable correctly."
            )
            exit(1)
        langfiles = list(map(lambda x: x.name, tesspath.glob("*.traineddata")))
        if not langfiles:
            print(
                "No language packs found, please make sure you have set the TESSDATA_PREFIX environment variable correctly."
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
        self.engine = PyTessBaseAPI(lang=langstring)  # type: ignore
        self.engine.SetVariable("debug_file", os.devnull)
        self.engine.SetVariable("psm", "6")
        if blacklist:
            self.engine.SetVariable("tessedit_char_blacklist", blacklist)

    def get_ocr_text(self, im: Image.Image) -> str:
        self.engine.SetImage(im)
        return self.engine.GetUTF8Text().strip()

    def quit(self):
        self.engine.End()
