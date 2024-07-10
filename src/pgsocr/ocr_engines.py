from pathlib import Path
import os
from PIL import Image

from tesserocr import PyTessBaseAPI
from mistralrs import Runner, Which, ChatCompletionRequest, VisionArchitecture


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
        self.engine = PyTessBaseAPI(lang=langstring)
        self.engine.SetVariable("debug_file", os.devnull)
        self.engine.SetVariable("psm", "6")
        if blacklist:
            self.engine.SetVariable("tessedit_char_blacklist", blacklist)

    def get_ocr_text(self, im: Image.Image) -> str:
        self.engine.SetImage(im)
        return self.engine.GetUTF8Text().strip()

    def quit(self):
        self.engine.End()


class Phi3OCREngine:
    def __init__(self):
        self.runner = Runner(
            which=Which.VisionPlain(
                model_id="microsoft/Phi-3-vision-128k-instruct",
                tokenizer_json=None,
                repeat_last_n=64,
                arch=VisionArchitecture.Phi3V,
            ),
        )

    def get_ocr_text(self, im: Image.Image) -> str:
        im.save("tmp.png")
        res = self.runner.send_chat_completion_request(
            ChatCompletionRequest(
                model="phi3v",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "tmp.png",
                                },
                            },
                            {
                                "type": "text",
                                "text": "<|image_1|>\nRead the text from the image, output just the text.",
                            },
                        ],
                    }
                ],
                max_tokens=256,
                presence_penalty=1.0,
                top_p=0.1,
                temperature=0.1,
            )
        )
        return res.choices[0].message.content
