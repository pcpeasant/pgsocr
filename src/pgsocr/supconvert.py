from . import img_utils
from .pgsparser import PGStream
from tqdm import tqdm


def generate_timecode(millis: int, fmt: str) -> str:
    seconds, milliseconds = divmod(millis, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if fmt == "srt":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    elif fmt == "ass":
        hundredths = milliseconds // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}:{hundredths:02d}"
    else:
        raise ValueError(f"Unknown format '{fmt}' specified.")


def sup2srt(in_path: str, out_path: str, ocr_engine) -> None:
    try:
        supfile = PGStream(in_path)
    except ValueError:
        print(f"{in_path} is not a SUP file.")
        return
    srtfile = open(f"{out_path}/{supfile.file_name.split('.')[0]}.srt", "w")
    seq_num = 1
    for img_obj in tqdm(
        img_utils.extract_images(supfile), desc=f"{supfile.file_name}", unit="lines"
    ):
        text = ocr_engine.get_ocr_text(img_utils.preprocess_image(img_obj.img))
        srtfile.write(
            f"{seq_num}\n{generate_timecode(img_obj.start_ms, 'srt')} --> {generate_timecode(img_obj.end_ms, 'srt')}\n{text}\n\n"
        )
        seq_num += 1

    ocr_engine.quit()
    srtfile.close()


def sup2ass(in_path: str, out_path: str, ocr_engine) -> None:
    try:
        supfile = PGStream(in_path)
    except ValueError:
        print(f"{in_path} is not a SUP file.")
        return
    assfile = open(f"{str(out_path)}/{supfile.file_name.split('.')[0]}.ass", "w")
    assfile.write(
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
    for img_obj in tqdm(
        img_utils.extract_images(supfile), desc=f"{supfile.file_name}", unit="lines"
    ):
        text = ocr_engine.get_ocr_text(img_utils.preprocess_image(img_obj.img))
        text = text.replace("\n", "\\N")
        posx = img_obj.x_pos + (img_obj.img.width) // 2
        posy = img_obj.y_pos + (img_obj.img.height) // 2
        assfile.write(
            f"Dialogue: 0,{generate_timecode(img_obj.start_ms, 'ass')},{generate_timecode(img_obj.end_ms, 'ass')},Default,,0,0,0,,{{\\an5}}{{\pos({posx}, {posy})}}{text}\n"
        )
    ocr_engine.quit()
    assfile.close()
