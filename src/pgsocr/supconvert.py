from . import utils
from pathlib import Path
from .pgsparser import PGStream
from tqdm import tqdm


def sup2srt(in_path: Path | str, out_path: str, ocr_engine) -> None:
    if isinstance(in_path, str):
        in_path = Path(in_path)
    if in_path.suffix != ".sup":
        print("File is not a SUP file, skipping")
        return
    supfile = PGStream(in_path)
    srtfile = open(f"{str(out_path)}/{in_path.stem}.srt", "w")
    seq_num = 1
    for img, start, end in tqdm(
        utils.extract_images(supfile), desc=f"{supfile.file_name}", unit="lines"
    ):
        text = ocr_engine.get_ocr_text(utils.preprocess_image(img))
        srtfile.write(
            f"{seq_num}\n{utils.generate_timecode(start)} --> {utils.generate_timecode(end)}\n{text}\n\n"
        )
        seq_num += 1

    ocr_engine.quit()
    srtfile.close()
