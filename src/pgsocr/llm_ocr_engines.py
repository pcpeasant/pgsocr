from pathlib import Path
import os
from PIL import Image

from mistralrs import Runner, Which, ChatCompletionRequest, VisionArchitecture


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
