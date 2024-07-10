from pathlib import Path
from .pgsparser import PGStream
from .utils import extract_images, generate_timecode, preprocess_image


def sup2srt(in_path: Path | str, out_path: str, ocr_engine) -> None:
    if isinstance(in_path, str):
        in_path = Path(in_path)
    if in_path.suffix != ".sup":
        print("File is not a SUP file, skipping")
        return
    supfile = PGStream(in_path)
    srtfile = open(f"{str(out_path)}/{in_path.stem}.srt", "w")
    print(f"Converting {supfile.file_name}...")
    seq_num = 1
    for img, start, end in extract_images(supfile):
        text = ocr_engine.get_ocr_text(preprocess_image(img))
        print(text)
        srtfile.write(
            f"{seq_num}\n{generate_timecode(start)} --> {generate_timecode(end)}\n{text}\n\n"
        )
        seq_num += 1

    ocr_engine.quit()
    srtfile.close()
