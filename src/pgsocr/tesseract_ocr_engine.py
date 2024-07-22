from pathlib import Path
import os
from PIL import Image

from tesserocr import PyTessBaseAPI, get_languages


class TesseractOCREngine:
    def __init__(self, requested_languages: list[str], blacklist: str):
        tesspath, available_languages = get_languages()
        tesspath = Path(tesspath)
        if not tesspath.exists() or not available_languages:
            print(
                f"Invalid tessdata path specified or the folder \"{tesspath.absolute()}\" doesn't contain any .traineddata file."
                " Make sure you have set the TESSDATA_PREFIX environment variable correctly."
            )
            exit(1)

        for l in requested_languages:
            if l not in available_languages:
                print(
                    f"Failed to load language '{l}', make sure you have specified the correct language code"
                    " and that the corresponding Tesseract language pack is installed on your system."
                )
                exit(1)
        langstring = "+".join(l for l in requested_languages)
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
