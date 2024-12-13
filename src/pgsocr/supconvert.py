from pgsocr import img_utils
from pgsocr.pgsparser import PGStream
from tqdm import tqdm
from typing import Optional


def generate_timecode(millis: int, fmt: str) -> str:
    seconds, milliseconds = divmod(millis, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if fmt == "srt":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    elif fmt == "ass":
        hundredths = milliseconds // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}.{hundredths:02d}"
    else:
        raise ValueError(f"Unknown format '{fmt}' specified.")


def supconvert(
    in_path: str,
    out_path: str,
    ocr_engine,
    fmt: str,
    img_dump_path: Optional[str] = None,
) -> None:
    try:
        supfile = PGStream(in_path)
    except ValueError:
        print(f"{in_path} is not a SUP file.")
        return

    file_name = supfile.file_name.split(".")[0]
    outfile = open(f"{out_path}/{file_name}.{fmt}", "w", buffering=1)
    if fmt == "ass":
        outfile.write(
            f"""
[Script Info]
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {supfile.res_width}
PlayResY: {supfile.res_height}
LayoutResX: {supfile.res_width}
LayoutResY: {supfile.res_height}
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,LTFinnegan Medium,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,3.6,1.5,2,200,200,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        )

    seq_num = 1
    for img_obj in tqdm(
        img_utils.extract_images(supfile), desc=f"{supfile.file_name}", unit="lines"
    ):
        if img_dump_path is not None:
            img_obj.img.save(
                f"{img_dump_path}/{img_obj.start_ms}-{img_obj.end_ms}_{seq_num}.png"
            )
        text = ocr_engine.get_ocr_text(img_utils.preprocess_image(img_obj.img))

        if fmt == "srt":
            outfile.write(
                f"{seq_num}\n{generate_timecode(img_obj.start_ms, 'srt')} --> {generate_timecode(img_obj.end_ms, 'srt')}\n{text}\n\n"
            )
            seq_num += 1
        elif fmt == "ass":
            text = text.replace("\n", "\\N")
            posx = img_obj.x_pos + (img_obj.img.width) // 2
            posy = img_obj.y_pos + (img_obj.img.height) // 2
            outfile.write(
                f"Dialogue: 0,{generate_timecode(img_obj.start_ms, 'ass')},{generate_timecode(img_obj.end_ms, 'ass')},Default,,0,0,0,,{{\\an5}}{{\\pos({posx}, {posy})}}{text}\n"
            )

    ocr_engine.quit()
    outfile.close()
