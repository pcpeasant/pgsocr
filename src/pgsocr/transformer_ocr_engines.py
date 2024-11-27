from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import os
import torch

# workaround for unnecessary flash_attn requirement
from unittest.mock import patch
from transformers.dynamic_module_utils import get_imports


def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
    imports = get_imports(filename)
    if not torch.cuda.is_available() and "flash_attn" in imports:
        imports.remove("flash_attn")
    return imports


class Florence2OCREngine:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        model_id = "microsoft/Florence-2-large-ft"
        with patch(
            "transformers.dynamic_module_utils.get_imports", fixed_get_imports
        ):  # workaround for unnecessary flash_attn requirement
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, attn_implementation="sdpa", trust_remote_code=True
            ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

    def get_ocr_text(self, im: Image.Image):
        task_prompt = "<OCR_WITH_REGION>"
        inputs = self.processor(text=task_prompt, images=im, return_tensors="pt")

        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"].to(self.device),
            pixel_values=inputs["pixel_values"].to(self.device),
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False,
        )
        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=False
        )[0]

        parsed_answer = self.processor.post_process_generation(
            generated_text, task=task_prompt, image_size=(im.width, im.height)
        )
        return "\n".join(
            s.replace("</s>", "").strip() for s in parsed_answer[task_prompt]["labels"]
        )

    def quit(self):
        pass
