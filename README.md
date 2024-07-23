# pgsocr
Convert Blu-Ray SUP subtitles to SRT or ASS using AI Language Models or Tesseract.

### Prerequisites

If planning on using Tesseract, see: https://tesseract-ocr.github.io/tessdoc/Installation.html \
Make sure to install all the required language packs and note down the location of the 'tessdata' directory. \
Make sure to set the TESSDATA_PREFIX environment variable to the location of the 'tessdata' directory from the previous step.

### Installation

Download the latest .whl from the Releases tab and install using pip. \
Make sure to install the [lm] extras if you want to use AI models.

### Usage:

    Options:
    -i: Specify the path to the SUP file or (batch mode) directory.
    -o: Specify the path to the output directory.
    -m: Specify the OCR engine to use (florence2 or tesseract).
    -l: (Only if using Tesseract) Specify the list of languages to use separated by spaces. Defaults to English.
    -b: (Only if using Tesseract) Specify a custom character blacklist for Tesseract. Enter an empty string to turn off the default blacklist.
    -f: Specify the output format (SRT or ASS). ASS output also has support for subtitle positioning.

    Note: Florence2 is more accurate than Tesseract but far more resource heavy and only works for English. A recent GPU with a large amount of VRAM is recommended.

    Examples:
    # Single file
    pgsocr -i /path/to/file -o path/to/outputdir -t /path/to/tessdata -m tesseract -l eng jpn

    # Multiple files in a directory
    pgsocr -i /path/to/inputdir -o /path/to/outputdir -t /path/to/tessdata -m florence2
