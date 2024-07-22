import os
from pathlib import Path
from PIL import Image
from platform import system

from tesserocr import PyTessBaseAPI, get_languages


class TesseractOCREngine:
    def __init__(self, requested_languages: list[str], blacklist: str):
        tesspath, available_languages = get_languages()
        tesspath = Path(tesspath)
        if not available_languages:
            system_name = system()

            # Try to find the system tessdata folder.
            # Based on https://tesseract-ocr.github.io/tessdoc/Installation.html
            possible_tessdata_folders: list[Path] = []
            if system_name == "Windows":
                possible_tessdata_folders = [
                    Path("C:\\Program Files\\Tesseract-OCR\\tessdata"),
                    Path("C:\\Program Files (x86)\\Tesseract-OCR\\tessdata")
                ]
            elif system_name == "Linux":
                possible_tessdata_folders = [
                    Path("/usr/share/tesseract-ocr/tessdata"),
                    Path("/usr/share/tessdata")
                ]

                # Verify if path like "/usr/share/tesseract-ocr/4.00/tessdata" exist
                default_installation_path = Path("/usr/share/tesseract-ocr")
                if default_installation_path.exists() and default_installation_path.is_dir():
                    for child in default_installation_path.iterdir():
                        if not child.is_dir():
                            continue
                        tessdata_folder = child.joinpath("tessdata")
                        if tessdata_folder.exists() and tessdata_folder.is_dir():
                            possible_tessdata_folders.append(tessdata_folder)
            elif system_name == "Darwin":
                # Verify if path like "/usr/local/Cellar/tesseract/3.05.02/share/tessdata" exist
                default_installation_path = Path("/usr/local/Cellar/tesseract")
                if default_installation_path.exists() and default_installation_path.is_dir():
                    for child in default_installation_path.iterdir():
                        if not child.is_dir():
                            continue
                        tessdata_folder = child.joinpath("share").joinpath("tessdata")
                        if tessdata_folder.exists() and tessdata_folder.is_dir():
                            possible_tessdata_folders.append(tessdata_folder)

            found_valid_tessdata_folder = False
            for tessdata_folder in possible_tessdata_folders:
                _, available_languages = get_languages(str(tessdata_folder))
                if available_languages:
                    tesspath = tessdata_folder
                    found_valid_tessdata_folder = True
                    break

            if not found_valid_tessdata_folder:
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
        self.engine = PyTessBaseAPI(path=str(tesspath), lang=langstring)  # type: ignore
        self.engine.SetVariable("debug_file", os.devnull)
        self.engine.SetVariable("psm", "6")
        if blacklist:
            self.engine.SetVariable("tessedit_char_blacklist", blacklist)

    def get_ocr_text(self, im: Image.Image) -> str:
        self.engine.SetImage(im)
        return self.engine.GetUTF8Text().strip()

    def quit(self):
        self.engine.End()
