# pgsocr
Convert Blu-Ray SUP subtitles to SRT using Tesseract or LLMs.

### Tesseract Installation

See: https://tesseract-ocr.github.io/tessdoc/Installation.html \
Make sure to install all the required language packs and note down the location of the 'tessdata' directory. \
Make sure to set the TESSDATA_PREFIX environment variable to the location of the 'tessdata' directory from the previous step.

### Usage:

    Options:
    -i: Specify the path to the SUP file or (batch mode) directory.
    -o: Specify the path to the output directory.
    -m: Specify the OCR engine to use (phi3v or tesseract).
    -l: (Only if using Tesseract) Specify the list of languages to use separated by commas. Defaults to English.
    -b: (Only if using Tesseract) Specify a custom character blacklist for Tesseract. Enter an empty string to turn off the default blacklist.

    Examples:
    # Single file
    pgsocr -i /path/to/file -o path/to/outputdir -t /path/to/tessdata -l eng,jpn

    # Multiple files in a directory
    pgsocr -i /path/to/inputdir -o /path/to/outputdir -t /path/to/tessdata
